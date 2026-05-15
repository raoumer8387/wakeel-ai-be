import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Get the base directory (root of the project)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    # Legal Agent Settings
    GEMINI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    DATA_PATH: str = "D:\\wakeel-ai-be\\Wakeel-AI-data"
    CHROMA_PERSIST_DIR: str = os.path.join(BASE_DIR, "chroma_db")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
