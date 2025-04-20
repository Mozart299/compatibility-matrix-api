# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from supabase import Client
from typing import Dict, Any

from app.db.supabase import get_supabase, get_admin_supabase
from app.models.user import UserCreate, UserLogin, TokenData

router = APIRouter()

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate, 
    supabase: Client = Depends(get_admin_supabase)
):
    """Register a new user with Supabase Auth"""
    try:
        # Register user with Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": user_in.email,
            "password": user_in.password
        })
        
        # If registration successful, create user metadata in profiles table
        if auth_response.user:
            user_id = auth_response.user.id
            
            # Insert user profile into the 'profiles' table
            profile_data = {
                "id": user_id,  # Use the same ID as auth
                "email": user_in.email,
                "name": user_in.name,
                "created_at": 'now()'  # Use PostgreSQL function
            }
            
            # Insert into profiles table
            supabase.table('profiles').insert(profile_data).execute()
            
            return {
                "detail": "Registration successful. Please check your email for verification.",
                "user_id": user_id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=TokenData)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    supabase: Client = Depends(get_supabase)
):
    """Login with Supabase Auth and get access token"""
    try:
        # Authenticate with Supabase
        auth_response = supabase.auth.sign_in_with_password({
            "email": form_data.username,  # OAuth2 form uses username field
            "password": form_data.password
        })
        
        # Extract tokens
        session = auth_response.session
        
        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/refresh", response_model=TokenData)
async def refresh_token(
    refresh_token: Dict[str, str],
    supabase: Client = Depends(get_supabase)
):
    """Refresh access token using refresh token"""
    try:
        # Use Supabase to refresh the token
        auth_response = supabase.auth.refresh_session(refresh_token["refresh_token"])
        
        # Extract new tokens
        session = auth_response.session
        
        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token refresh failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/logout")
async def logout(
    supabase: Client = Depends(get_supabase)
):
    """Logout user - invalidate session on Supabase"""
    try:
        # Sign out from Supabase
        supabase.auth.sign_out()
        return {"detail": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )

@router.post("/send-reset-password")
async def send_reset_password(
    email: Dict[str, str],
    supabase: Client = Depends(get_supabase)
):
    """Send password reset email"""
    try:
        supabase.auth.reset_password_email(email["email"])
        return {"detail": "Password reset email sent"}
    except Exception as e:
        # Don't reveal if the email exists or not for security
        return {"detail": "If the email exists, a password reset link has been sent"}