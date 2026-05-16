from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.auth import router as auth_router
from app.api.v1.endpoints.legal import router as legal_router
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(legal_router, prefix=f"{settings.API_V1_STR}/legal", tags=["Legal Agent"])

@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI Google Auth API", "docs": "/docs"}

@app.get("/api/v1/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Test protected route
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "avatar_url": current_user.avatar_url
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8100, reload=True)
