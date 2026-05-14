from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import jwt, JWTError
import bcrypt

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    GoogleLoginRequest,
    ManualRegisterRequest,
    ManualLoginRequest,
    TokenResponse,
    RefreshRequest,
)
from app.services.google_auth import verify_google_token
from app.api.v1.deps import get_current_user

router = APIRouter()

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_byte_enc = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_byte_enc, hashed_password_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict):
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)


# ──────────────────────────────────────────────
#  POST /api/v1/auth/google
# ──────────────────────────────────────────────
@router.post("/google", response_model=TokenResponse)
async def google_auth(
    request: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate via Google ID token. Creates user if first time, updates profile otherwise."""

    # 1. Verify Google Token
    google_user = verify_google_token(request.id_token)

    google_id = google_user["sub"]
    email = google_user["email"]
    name = google_user.get("name", "")
    avatar_url = google_user.get("picture")

    # 2. Upsert user
    result = await db.execute(select(User).filter(User.google_id == google_id))
    user = result.scalars().first()

    if user:
        # Update profile in case it changed on Google
        user.name = name
        user.avatar_url = avatar_url
    else:
        user = User(
            google_id=google_id,
            email=email,
            name=name,
            avatar_url=avatar_url,
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    # 3. Issue tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {"access_token": access_token, "refresh_token": refresh_token, "user": user}


# ──────────────────────────────────────────────
#  POST /api/v1/auth/register
# ──────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse)
async def register(
    request: ManualRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user with name, email, phone, and password."""

    # Check if email already exists
    result = await db.execute(select(User).filter(User.email == request.email))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    # Check if phone already exists (if provided)
    if request.phone:
        result = await db.execute(select(User).filter(User.phone == request.phone))
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this phone number already exists",
            )

    user = User(
        name=request.name,
        email=request.email,
        phone=request.phone,
        hashed_password=hash_password(request.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {"access_token": access_token, "refresh_token": refresh_token, "user": user}


# ──────────────────────────────────────────────
#  POST /api/v1/auth/login
# ──────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(
    request: ManualLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login with email and password."""

    result = await db.execute(select(User).filter(User.email == request.email))
    user = result.scalars().first()

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {"access_token": access_token, "refresh_token": refresh_token, "user": user}


# ──────────────────────────────────────────────
#  POST /api/v1/auth/refresh
# ──────────────────────────────────────────────
@router.post("/refresh")
async def refresh_token(request: RefreshRequest):
    """Exchange a valid refresh token for a new access token."""

    try:
        payload = jwt.decode(
            request.refresh_token,
            settings.JWT_SECRET,
            algorithms=[settings.ALGORITHM],
        )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
        )

    access_token = create_access_token(data={"sub": user_id})
    return {"access_token": access_token}


# ──────────────────────────────────────────────
#  POST /api/v1/auth/logout
# ──────────────────────────────────────────────
@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout the user.
    Since we are using stateless JWTs, the actual logout process must happen on the client side
    by deleting the access and refresh tokens from secure storage.
    """
    return {"message": "Successfully logged out. Please remove the tokens from your client storage."}

