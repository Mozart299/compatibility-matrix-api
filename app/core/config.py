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
    SUPABASE_SERVICE_KEY: str  
    
    # Google OAuth settings
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    
    # CORS - Ensure all necessary origins are included
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://compatibility-matrix.vercel.app",
        "https://random-maria-mozart299-46512b0e.koyeb.app"
    ]
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True
    }

# Create settings instance
settings = Settings()