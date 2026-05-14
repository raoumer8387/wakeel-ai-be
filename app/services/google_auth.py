from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import HTTPException, status
from app.config import settings

def verify_google_token(token: str) -> dict:
    try:
        # Specify the CLIENT_ID of the app that accesses the backend:
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )

        # ID token is valid. Get the user's Google Account ID from the decoded token.
        # idinfo['sub'] is the unique google_id
        return idinfo
    except ValueError as e:
        # Invalid token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
