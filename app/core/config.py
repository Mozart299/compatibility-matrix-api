# app/core/config.py
from pydantic import BaseSettings, PostgresDsn, validator
import secrets
from typing import Optional, Dict, Any

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Compatibility Matrix"
    API_V1_STR: str = "/api/v1"
    
    # Security
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_REFRESH_SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # 15 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7     # 7 days
    
    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: Optional[PostgresDsn] = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]  # React default port
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()