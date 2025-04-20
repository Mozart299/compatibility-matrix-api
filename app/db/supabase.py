# app/db/supabase.py
from supabase import create_client, Client
from app.core.config import settings

# Debug: Print settings to verify
print("SUPABASE_URL:", settings.SUPABASE_URL)
print("SUPABASE_KEY:", settings.SUPABASE_KEY)
print("SUPABASE_SERVICE_KEY:", settings.SUPABASE_SERVICE_KEY)

# Validate inputs
if not all([settings.SUPABASE_URL, settings.SUPABASE_KEY, settings.SUPABASE_SERVICE_KEY]):
    missing = [k for k, v in {
        "SUPABASE_URL": settings.SUPABASE_URL,
        "SUPABASE_KEY": settings.SUPABASE_KEY,
        "SUPABASE_SERVICE_KEY": settings.SUPABASE_SERVICE_KEY
    }.items() if not v]
    raise ValueError(f"Missing or empty Supabase settings: {missing}")

# Create a Supabase client
try:
    supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    print("Supabase client initialized successfully")
except Exception as e:
    print(f"Failed to initialize Supabase client: {e}")
    raise

# Create an admin client with service role key
try:
    admin_supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    print("Admin Supabase client initialized successfully")
except Exception as e:
    print(f"Failed to initialize Admin Supabase client: {e}")
    raise

def get_supabase():
    """Dependency to get Supabase client"""
    return supabase

def get_admin_supabase():
    """Dependency to get Supabase admin client with service role key"""
    return admin_supabase