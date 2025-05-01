# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Query, Form
from fastapi.security import OAuth2PasswordRequestForm
from supabase import Client
from typing import Dict, Any, Optional

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
    code_verifier: Optional[str] = Query(None),
    supabase: Client = Depends(get_admin_supabase)
):
    """
    Initiate Google OAuth login flow
    
    Optional query parameter:
    - code_verifier: Optional PKCE code verifier
    """
    try:
        # Use Supabase to get the Google auth URL
        options = {
            "provider": "google",
            "redirect_to": settings.GOOGLE_REDIRECT_URI,
            "scopes": "email profile"
        }
        
        # Include flow_state for code verifier if provided
        if code_verifier:
            options["flow_state"] = code_verifier
            
        auth_url = supabase.auth.sign_in_with_oauth(options)
        
        return {"auth_url": auth_url}
    except Exception as e:
        print(f"Error in Google Auth: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initiating Google auth: {str(e)}"
        )

@router.post("/callback/google")
async def google_callback(
    code: str = Form(...),
    code_verifier: Optional[str] = Form(None),
    supabase: Client = Depends(get_admin_supabase)
):
    """
    Handle Google OAuth callback
    
    This endpoint is called by the Next.js frontend after receiving the auth code from Google.
    """
    try:
        print(f"Received Google auth code: {code[:10]}...")
        if code_verifier:
            masked_verifier = code_verifier[:5] + "..." + code_verifier[-5:] if len(code_verifier) > 10 else "***"
            print(f"Code verifier received: {masked_verifier}")

        # Exchange code for session using Supabase
        exchange_params = {
            "auth_code": code,
            "provider": "google"
        }
        if code_verifier:
            exchange_params["code_verifier"] = code_verifier

        session_response = supabase.auth.exchange_code_for_session(exchange_params)
        
        if not session_response or not session_response.session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to authenticate with Google: No session returned"
            )

        session = session_response.session
        access_token = session.access_token
        refresh_token = session.refresh_token

        # Check if user exists in profiles table, create if not
        try:
            user = supabase.auth.get_user(access_token)
            user_id = user.user.id
            email = user.user.email

            # Extract name from user metadata or fallback to email username
            name = None
            if user.user.user_metadata:
                name = (
                    user.user.user_metadata.get("full_name")
                    or user.user.user_metadata.get("name")
                    or user.user.user_metadata.get("preferred_username")
                )
            if not name:
                name = email.split("@")[0]

            # Check if profile exists
            profile_check = supabase.table("profiles").select("id").eq("id", user_id).execute()

            if not profile_check.data:
                # Create a new profile
                profile_data = {
                    "id": user_id,
                    "email": email,
                    "name": name,
                    "created_at": "now()",
                    "updated_at": "now()"
                }
                supabase.table("profiles").insert(profile_data).execute()
                print(f"Created new profile for user: {user_id}")
            else:
                print(f"User profile already exists: {user_id}")

        except Exception as profile_error:
            print(f"Error creating/checking profile: {str(profile_error)}")
            # Continue with authentication even if profile creation fails

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    except Exception as e:
        print(f"Error in Google callback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error handling Google callback: {str(e)}"
        )