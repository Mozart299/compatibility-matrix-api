# app/core/config.py
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Compatibility Matrix"
    API_V1_STR: str = "/api/v1"
    
    # Supabase settings
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str  # Service/admin key for server-side operations
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]  # React default port
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True
    }

# Create settings instance
settings = Settings()