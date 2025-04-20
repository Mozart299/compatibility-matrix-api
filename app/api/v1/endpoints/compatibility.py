# app/api/v1/endpoints/compatibility.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from supabase import Client

from app.api.dependencies.auth import get_current_user
from app.db.supabase import get_supabase

router = APIRouter()

@router.get("/matrix")
async def get_compatibility_matrix(
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Get compatibility matrix for the current user"""
    try:
        user_id = current_user.id
        
        # Query compatibility scores from Supabase
        response = supabase.table('compatibility_scores') \
            .select('*') \
            .filter(f'user_id_a.eq.{user_id} or user_id_b.eq.{user_id}') \
            .execute()
            
        # This will get all scores where the current user is either user_a or user_b
        
        if not response.data:
            return {"scores": []}
            
        return {"scores": response.data}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching compatibility matrix: {str(e)}"
        )

@router.get("/{user_id}")
async def get_compatibility_with_user(
    user_id: str,
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Get compatibility details with a specific user"""
    try:
        current_user_id = current_user.id
        
        # Query compatibility scores between the two users
        response = supabase.table('compatibility_scores') \
            .select('*') \
            .filter(
                f'(user_id_a.eq.{current_user_id} and user_id_b.eq.{user_id}) or ' +
                f'(user_id_a.eq.{user_id} and user_id_b.eq.{current_user_id})'
            ) \
            .execute()
            
        if not response.data or len(response.data) == 0:
            return {
                "overall_score": 0,
                "dimension_scores": [],
                "message": "No compatibility data available yet"
            }
            
        # Process compatibility data
        compatibility_data = response.data[0]
        
        # Also get the other user's profile
        user_response = supabase.table('profiles').select('name').eq('id', user_id).execute()
        other_user_name = user_response.data[0]['name'] if user_response.data else "Unknown User"
        
        return {
            "overall_score": compatibility_data.get("overall_score", 0),
            "dimension_scores": compatibility_data.get("dimension_scores", []),
            "strengths": compatibility_data.get("strengths", []),
            "challenges": compatibility_data.get("challenges", []),
            "other_user_name": other_user_name
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching compatibility data: {str(e)}"
        )

@router.get("/report/{user_id}")
async def get_detailed_compatibility_report(
    user_id: str,
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Get detailed compatibility report with another user"""
    try:
        # This would be a more detailed version of the compatibility data
        # For now, it's a placeholder that would be expanded with more detailed data
        
        # Basic compatibility info
        compatibility_info = await get_compatibility_with_user(user_id, current_user, supabase)
        
        # Add more detailed information that would be shown in a full report
        compatibility_info["detailed_analysis"] = {
            "personality_comparison": {
                "description": "Analysis of how your personalities interact",
                "data": {}  # Would contain detailed personality comparison data
            },
            "values_alignment": {
                "description": "Analysis of shared and differing values",
                "data": {}  # Would contain values alignment data
            },
            "communication_dynamics": {
                "description": "Analysis of communication style compatibility",
                "data": {}  # Would contain communication dynamics data
            }
        }
        
        return compatibility_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating compatibility report: {str(e)}"
        )