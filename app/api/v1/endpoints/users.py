# app/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from supabase import Client

from app.api.dependencies.auth import get_current_user, get_optional_user
from app.db.supabase import get_supabase, get_admin_supabase

router = APIRouter()

@router.get("/me")
async def get_my_profile(
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Get current user's profile from Supabase"""
    try:
        # Get user profile from profiles table using auth user ID
        user_id = current_user.id
        
        response = supabase.table('profiles').select('*').eq('id', user_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
            
        return response.data[0]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching profile: {str(e)}"
        )

@router.put("/me")
async def update_profile(
    profile_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Update current user's profile in Supabase"""
    try:
        user_id = current_user.id
        
        # Filter out fields that shouldn't be updated directly
        safe_data = {k: v for k, v in profile_data.items() 
                    if k in ["name", "bio", "avatar_url", "location"]}
        
        # Update profile in the database
        response = supabase.table('profiles').update(safe_data).eq('id', user_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found or update failed"
            )
            
        return response.data[0]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating profile: {str(e)}"
        )

@router.get("/{user_id}")
async def get_user_by_id(
    user_id: str,
    current_user: Dict = Depends(get_optional_user),
    supabase: Client = Depends(get_supabase)
):
    """Get a user by ID from Supabase"""
    try:
        # Get profile from database
        response = supabase.table('profiles').select('*').eq('id', user_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        # Filter out private fields if not the current user
        profile = response.data[0]
        if not current_user or current_user.id != user_id:
            # Remove private fields based on your app's privacy rules
            # This is a simple example - adjust based on your requirements
            if "email" in profile:
                profile.pop("email")
                
        return profile
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user: {str(e)}"
        )