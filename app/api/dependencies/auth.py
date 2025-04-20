# app/api/dependencies/auth.py
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.db.supabase import get_supabase, get_admin_supabase
from supabase import Client

# HTTP Bearer scheme for token extraction
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: Client = Depends(get_admin_supabase)
):
    """
    Dependency to get the current authenticated user from Supabase.
    Validates the JWT token and returns the user data.
    """
    try:
        # Extract token from Authorization header
        token = credentials.credentials
        
        # Verify the token and get user data
        # Using admin_supabase to avoid permissions issues
        response = supabase.auth.get_user(token)
        user = response.user
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Return the user data
        return user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_optional_user(
    authorization: Optional[str] = Header(None),
    supabase: Client = Depends(get_admin_supabase)
):
    """
    Dependency to optionally get the current user.
    Used for endpoints that work with or without authentication.
    """
    if not authorization:
        return None
        
    try:
        # Extract token from Authorization header
        # The header format should be "Bearer {token}"
        token = authorization.split(" ")[1]
        
        # Verify the token and get user data
        response = supabase.auth.get_user(token)
        return response.user
    except:
        # If any error occurs, just return None instead of raising an exception
        return None