from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, field_validator
import secrets
from typing import Optional, Any, Union
from pydantic_core.core_schema import ValidationInfo

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

    @field_validator("DATABASE_URL", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            username=info.data.get("POSTGRES_USER"),
            password=info.data.get("POSTGRES_PASSWORD"),
            host=info.data.get("POSTGRES_SERVER"),
            path=f"/{info.data.get('POSTGRES_DB') or ''}",
        )
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]  # React default port
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True
    }

# Create settings instance
settings = Settings()