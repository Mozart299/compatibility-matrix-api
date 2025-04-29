# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from supabase import Client
from typing import Dict, Any

from app.db.supabase import get_supabase, get_admin_supabase
from app.models.user import UserCreate, UserLogin, TokenData
from app.core.config import settings

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
        
        # Check if registration was successful
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed: No user created"
            )
        
        # If registration successful, create user metadata in profiles table
        user_id = auth_response.user.id
        
        # Insert user profile into the 'profiles' table
        profile_data = {
            "id": user_id,
            "email": user_in.email,
            "name": user_in.name,
        }
        
        # Insert into profiles table
        profile_response = supabase.table('profiles').insert(profile_data).execute()
        
        # Check if profile insertion was successful
        if not profile_response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user profile"
            )
        
        return {
            "detail": "Registration successful.",
            "user_id": user_id
        }
            
    except Exception as e:
        # Log the error for debugging
        print(f"Registration error: {str(e)}")
        # Handle specific Supabase Auth errors
        error_message = str(e).lower()
        if "already registered" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        if "password" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet requirements"
            )
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

@router.get("/login/google")
async def login_google(
    supabase: Client = Depends(get_admin_supabase)
):
    """
    Initiate Google OAuth login flow
    """
    try:
        # Use Supabase to get the Google auth URL
        auth_url = supabase.auth.get_url_for_provider(
            "google",
            {
                "redirect_to": settings.GOOGLE_REDIRECT_URI,
                "scopes": "email profile"
            }
        )
        
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initiating Google auth: {str(e)}"
        )

@router.post("/callback/google")
async def google_callback(
    request: Request,
    supabase: Client = Depends(get_admin_supabase)
):
    """
    Handle Google OAuth callback
    """
    try:
        # Get the query parameters from the request
        form_data = await request.form()
        
        # Extract code from request
        code = form_data.get("code")
        
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code not provided"
            )
        
        # Exchange code for tokens using Supabase
        auth_response = supabase.auth.exchange_code_for_session({
            "auth_code": code
        })
        
        # Create JWT token
        session = auth_response.session
        access_token = session.access_token
        refresh_token = session.refresh_token
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during Google callback: {str(e)}"
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