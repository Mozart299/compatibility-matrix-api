# app/db/supabase.py
from supabase import create_client, Client
from app.core.config import settings

# Create a Supabase client
supabase: Client = create_client(
    settings.SUPABASE_URL, 
    settings.SUPABASE_KEY
)

# Create an admin client with service role key
# This is used for server-side operations that need higher privileges
admin_supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_KEY
)

def get_supabase():
    """Dependency to get Supabase client"""
    return supabase

def get_admin_supabase():
    """Dependency to get Supabase admin client with service role key"""
    return admin_supabase