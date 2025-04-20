# app/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.dependencies.auth import get_current_user, get_current_active_verified_user
from app.db.database import get_db
from app.models.user import User, UserResponse
from app.services.auth import AuthService

router = APIRouter()

@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile"""
    return current_user

@router.put("/me", response_model=UserResponse)
def update_profile(
    user_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    # Get current user from database
    user = db.query(User).filter(User.id == current_user.id).first()
    
    # Update allowed fields
    if "name" in user_data:
        user.name = user_data["name"]
    
    # Commit changes
    db.commit()
    db.refresh(user)
    
    return user

@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db)
):
    """Get a user by ID"""
    user = AuthService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user