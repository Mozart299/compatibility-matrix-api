# app/api/v1/endpoints/compatibility.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from supabase import Client

from app.api.dependencies.auth import get_current_user
from app.db.supabase import get_supabase

router = APIRouter()

@router.get("/matrix")
async def get_compatibility_matrix(
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
    dimension_id: Optional[str] = None,
    min_score: Optional[int] = None
):
    """
    Get compatibility matrix for the current user
    
    Optional parameters:
    - dimension_id: Filter by specific dimension
    - min_score: Filter by minimum score
    """
    try:
        user_id = current_user.id
        
        # Validate dimension_id if provided
        if dimension_id:
            dimension_check = supabase.table('assessment_dimensions') \
                .select('id') \
                .eq('id', dimension_id) \
                .execute()
                
            if not dimension_check.data or len(dimension_check.data) == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dimension not found"
                )
        
        # Get users who have completed assessments with simplified logic
        if dimension_id:
            # Get users who have completed this specific dimension
            assessments_response = supabase.table('user_assessments') \
                .select('user_id') \
                .eq('status', 'completed') \
                .eq('dimension_id', dimension_id) \
                .execute()
        else:
            # Get users who have completed any assessment
            assessments_response = supabase.table('user_assessments') \
                .select('user_id') \
                .eq('status', 'completed') \
                .execute()
        
        # Extract unique user IDs who have completed assessments
        user_ids = list(set(assessment['user_id'] for assessment in assessments_response.data))
        
        # Handle case with no users
        if len(user_ids) == 0:
            dimension_info = None
            if dimension_id:
                dimension_response = supabase.table('assessment_dimensions') \
                    .select('*') \
                    .eq('id', dimension_id) \
                    .execute()
                    
                if dimension_response.data:
                    dimension_info = dimension_response.data[0]
                    
            return {
                "matrix": [],
                "dimension": dimension_info,
                "total_users": 0,
                "message": "No users have completed this dimension's assessment yet."
            }
        
        # Get all relevant users' profiles
        profiles_response = supabase.table('profiles') \
            .select('id, name, avatar_url') \
            .in_('id', user_ids) \
            .execute()
            
        profiles = profiles_response.data
        
        # Add current user if not in list
        if user_id not in user_ids:
            current_user_profile = supabase.table('profiles') \
                .select('id, name, avatar_url') \
                .eq('id', user_id) \
                .execute()
                
            if current_user_profile.data:
                profiles.append(current_user_profile.data[0])
                user_ids.append(user_id)
        
        # Query compatibility scores
        compatibility_query = supabase.table('compatibility_scores') \
            .select('*') \
            .or_(f'user_id_a.eq.{user_id},user_id_b.eq.{user_id}')
            
        # Add score filter if specified
        if min_score is not None:
            compatibility_query = compatibility_query.gte('overall_score', min_score)
        
        compatibility_response = compatibility_query.execute()
        compatibility_data = compatibility_response.data
        
        # Create the compatibility matrix
        matrix = []
        for profile in profiles:
            profile_id = profile['id']
            profile_scores = []
            
            for other_profile in profiles:
                other_id = other_profile['id']
                
                # Find compatibility score between these users
                score_entry = None
                
                # Self-compatibility is always 100%
                if profile_id == other_id:
                    score_entry = {
                        "score": 100,
                        "dimension_scores": []
                    }
                else:
                    # Check both possible orderings of user IDs
                    for entry in compatibility_data:
                        if ((entry['user_id_a'] == profile_id and entry['user_id_b'] == other_id) or 
                            (entry['user_id_a'] == other_id and entry['user_id_b'] == profile_id)):
                            
                            # If filtering by dimension, extract just that dimension's score
                            if dimension_id:
                                dimension_scores = entry.get('dimension_scores', [])
                                dimension_score = next(
                                    (d['score'] for d in dimension_scores if d['dimension_id'] == dimension_id), 
                                    None
                                )
                                
                                if dimension_score is not None:
                                    score_entry = {
                                        "score": dimension_score,
                                        "dimension_id": dimension_id
                                    }
                            else:
                                score_entry = {
                                    "score": entry['overall_score'],
                                    "dimension_scores": entry.get('dimension_scores', [])
                                }
                            
                            break
                
                if not score_entry:
                    # No compatibility data available
                    score_entry = {
                        "score": None,
                        "message": "No compatibility data available"
                    }
                
                profile_scores.append({
                    "user_id": other_id,
                    "name": other_profile['name'],
                    "avatar_url": other_profile.get('avatar_url'),
                    **score_entry
                })
            
            matrix.append({
                "user_id": profile_id,
                "name": profile['name'],
                "avatar_url": profile.get('avatar_url'),
                "scores": profile_scores
            })
        
        # Get dimension information if filtering by dimension
        dimension_info = None
        if dimension_id:
            dimension_response = supabase.table('assessment_dimensions') \
                .select('*') \
                .eq('id', dimension_id) \
                .execute()
                
            if dimension_response.data:
                dimension_info = dimension_response.data[0]
            
        return {
            "matrix": matrix,
            "dimension": dimension_info,
            "total_users": len(profiles)
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Add detailed error information for debugging
        error_detail = f"Error fetching compatibility matrix: {str(e)}\n"
        error_detail += f"User ID: {user_id}, "
        error_detail += f"Dimension ID: {dimension_id}, "
        error_detail += f"Min Score: {min_score}"
        
        print(error_detail)  # For server logs
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching compatibility matrix. Please try again."
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
        
        # Ensure user exists
        user_response = supabase.table('profiles') \
            .select('name, avatar_url') \
            .eq('id', user_id) \
            .execute()
            
        if not user_response.data or len(user_response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        other_user = user_response.data[0]
        
        # Get compatibility scores between the two users
        # Ensure user_id_a is always lexicographically less than user_id_b
        # This helps maintain the uniqueness constraint in the DB
        if current_user_id < user_id:
            user_id_a = current_user_id
            user_id_b = user_id
        else:
            user_id_a = user_id
            user_id_b = current_user_id
            
        response = supabase.table('compatibility_scores') \
            .select('*') \
            .eq('user_id_a', user_id_a) \
            .eq('user_id_b', user_id_b) \
            .execute()
            
        # If no compatibility data exists yet
        if not response.data or len(response.data) == 0:
            # Check if both users have completed any assessments
            assessments_query = supabase.table('user_assessments') \
                .select('dimension_id, user_id') \
                .eq('status', 'completed') \
                .in_('user_id', [current_user_id, user_id]) \
                .execute()
                
            if not assessments_query.data:
                return {
                    "overall_score": 0,
                    "dimension_scores": [],
                    "strengths": [],
                    "challenges": [],
                    "completed_assessments": 0,
                    "other_user": {
                        "id": user_id,
                        "name": other_user['name'],
                        "avatar_url": other_user.get('avatar_url')
                    },
                    "message": "Complete assessments to see compatibility scores"
                }
                
            # Check for dimensions that both users have completed
            current_user_dimensions = [a['dimension_id'] for a in assessments_query.data if a['user_id'] == current_user_id]
            other_user_dimensions = [a['dimension_id'] for a in assessments_query.data if a['user_id'] == user_id]
            
            shared_dimensions = set(current_user_dimensions).intersection(set(other_user_dimensions))
            
            if not shared_dimensions:
                return {
                    "overall_score": 0,
                    "dimension_scores": [],
                    "strengths": [],
                    "challenges": [],
                    "completed_assessments": len(current_user_dimensions),
                    "other_user_assessments": len(other_user_dimensions),
                    "shared_assessments": 0,
                    "other_user": {
                        "id": user_id,
                        "name": other_user['name'],
                        "avatar_url": other_user.get('avatar_url')
                    },
                    "message": "No shared completed assessments yet"
                }
                
            # Get the dimensions information
            dimensions_response = supabase.table('assessment_dimensions') \
                .select('id, name, description') \
                .in_('id', list(shared_dimensions)) \
                .execute()
                
            return {
                "overall_score": 0,
                "dimension_scores": [],
                "strengths": [],
                "challenges": [],
                "completed_assessments": len(current_user_dimensions),
                "other_user_assessments": len(other_user_dimensions),
                "shared_assessments": len(shared_dimensions),
                "shared_dimensions": dimensions_response.data,
                "other_user": {
                    "id": user_id,
                    "name": other_user['name'],
                    "avatar_url": other_user.get('avatar_url')
                },
                "message": "Compatibility calculation in progress"
            }
        
        # Process compatibility data
        compatibility_data = response.data[0]
        
        # Get dimension information for each dimension score
        dimension_ids = [d["dimension_id"] for d in compatibility_data.get("dimension_scores", [])]
        
        dimensions_map = {}
        if dimension_ids:
            dimensions_response = supabase.table('assessment_dimensions') \
                .select('id, name, description') \
                .in_('id', dimension_ids) \
                .execute()
                
            dimensions_map = {d["id"]: d for d in dimensions_response.data}
            
        # Enhance dimension scores with dimension information
        enhanced_dimension_scores = []
        for score in compatibility_data.get("dimension_scores", []):
            dimension_id = score["dimension_id"]
            if dimension_id in dimensions_map:
                enhanced_dimension_scores.append({
                    **score,
                    "name": dimensions_map[dimension_id]["name"],
                    "description": dimensions_map[dimension_id]["description"]
                })
            else:
                enhanced_dimension_scores.append(score)
        
        # Enhance strengths and challenges with dimension information
        enhanced_strengths = []
        for strength in compatibility_data.get("strengths", []):
            dimension_id = strength["dimension_id"]
            if dimension_id in dimensions_map:
                enhanced_strengths.append({
                    **strength,
                    "name": dimensions_map[dimension_id]["name"],
                    "description": dimensions_map[dimension_id]["description"]
                })
            else:
                enhanced_strengths.append(strength)
                
        enhanced_challenges = []
        for challenge in compatibility_data.get("challenges", []):
            dimension_id = challenge["dimension_id"]
            if dimension_id in dimensions_map:
                enhanced_challenges.append({
                    **challenge,
                    "name": dimensions_map[dimension_id]["name"],
                    "description": dimensions_map[dimension_id]["description"]
                })
            else:
                enhanced_challenges.append(challenge)
        
        return {
            "overall_score": compatibility_data.get("overall_score", 0),
            "dimension_scores": enhanced_dimension_scores,
            "strengths": enhanced_strengths,
            "challenges": enhanced_challenges,
            "other_user": {
                "id": user_id,
                "name": other_user['name'],
                "avatar_url": other_user.get('avatar_url')
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Add detailed error information
        error_detail = f"Error fetching compatibility data: {str(e)}\n"
        error_detail += f"Current User ID: {current_user_id}, "
        error_detail += f"Other User ID: {user_id}"
        
        print(error_detail)  # For server logs
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching compatibility data. Please try again."
        )

@router.get("/report/{user_id}")
async def get_detailed_compatibility_report(
    user_id: str,
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Get detailed compatibility report with another user"""
    try:
        # Get basic compatibility data
        compatibility_data = await get_compatibility_with_user(user_id, current_user, supabase)
        
        # Get user profiles for both users
        current_user_profile = supabase.table('profiles') \
            .select('*') \
            .eq('id', current_user.id) \
            .execute()
        
        other_user_profile = supabase.table('profiles') \
            .select('*') \
            .eq('id', user_id) \
            .execute()
            
        if not current_user_profile.data or not other_user_profile.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
            
        current_user_data = current_user_profile.data[0]
        other_user_data = other_user_profile.data[0]
        
        # Get shared interests
        current_user_interests = current_user_data.get('interests', [])
        other_user_interests = other_user_data.get('interests', [])
        
        # Handle case where interests might be None instead of empty list
        if current_user_interests is None:
            current_user_interests = []
        if other_user_interests is None:
            other_user_interests = []
            
        shared_interests = list(set(current_user_interests) & set(other_user_interests))
        unique_current_interests = list(set(current_user_interests) - set(other_user_interests))
        unique_other_interests = list(set(other_user_interests) - set(current_user_interests))
        
        # Get personality summaries if available
        personality_comparison = None
        if current_user_data.get('personality_summary') and other_user_data.get('personality_summary'):
            personality_comparison = {
                "user": current_user_data['personality_summary'],
                "other": other_user_data['personality_summary']
            }
            
        # Get communication styles if available
        communication_dynamics = None
        if current_user_data.get('communication_style') and other_user_data.get('communication_style'):
            communication_dynamics = {
                "user": current_user_data['communication_style'],
                "other": other_user_data['communication_style'],
                "dynamics": generate_communication_dynamics(
                    current_user_data['communication_style'],
                    other_user_data['communication_style']
                )
            }
            
        # Add additional information to the report
        detailed_report = {
            **compatibility_data,
            "interests": {
                "shared": shared_interests,
                "user": unique_current_interests,
                "other": unique_other_interests
            },
            "detailed_analysis": {
                "personality_comparison": personality_comparison,
                "communication_dynamics": communication_dynamics,
                "values_alignment": None  # Would be populated if values data is available
            }
        }
        
        return detailed_report
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Add detailed error information
        error_detail = f"Error generating compatibility report: {str(e)}\n"
        error_detail += f"Current User ID: {current_user.id}, "
        error_detail += f"Other User ID: {user_id}"
        
        print(error_detail)  # For server logs
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating compatibility report. Please try again."
        )

def generate_communication_dynamics(user_style, other_style):
    """
    Generate description of communication dynamics between two communication styles
    This is a simplified version that would be expanded in production
    """
    # Map of communication style combinations and their dynamics
    dynamics_map = {
        ("Direct", "Direct"): "You both communicate in a straightforward manner. This can lead to efficient communication but may sometimes lack sensitivity.",
        ("Direct", "Diplomatic"): "Your direct style paired with their diplomatic approach can create balanced conversations when both styles are respected. You may help them be more straightforward, while they can help you consider how messages might be received.",
        ("Diplomatic", "Direct"): "Your diplomatic style paired with their direct approach can create balanced conversations when both styles are respected. They may help you be more straightforward, while you can help them consider how messages might be received.",
        ("Diplomatic", "Diplomatic"): "You both prefer diplomatic communication that prioritizes harmony. This can create a supportive environment but may sometimes lead to issues being understated.",
        ("Analytical", "Analytical"): "You both communicate with a focus on facts and details. This creates clarity but may sometimes lack emotional warmth.",
        ("Analytical", "Direct"): "Your analytical style combined with their directness can be efficient for problem-solving but may create tension if emotional aspects are overlooked.",
        ("Direct", "Analytical"): "Your direct style combined with their analytical approach can be efficient for problem-solving but may create tension if emotional aspects are overlooked.",
        ("Analytical", "Diplomatic"): "Your analytical style paired with their diplomatic approach can balance detail-orientation with sensitivity to others.",
        ("Diplomatic", "Analytical"): "Your diplomatic style paired with their analytical approach can balance sensitivity to others with detail-orientation.",
        ("Expressive", "Expressive"): "You both communicate in an animated, emotionally open way. This creates engagement but may sometimes overwhelm others.",
        ("Expressive", "Direct"): "Your expressive style with their directness creates a dynamic where you bring enthusiasm and they bring focus.",
        ("Direct", "Expressive"): "Your direct style with their expressiveness creates a dynamic where you bring focus and they bring enthusiasm.",
        ("Expressive", "Diplomatic"): "Your expressive style combined with their diplomatic approach balances enthusiasm with harmony-seeking.",
        ("Diplomatic", "Expressive"): "Your diplomatic style combined with their expressive approach balances harmony-seeking with enthusiasm.",
        ("Expressive", "Analytical"): "Your expressive style paired with their analytical approach combines emotional engagement with factual precision.",
        ("Analytical", "Expressive"): "Your analytical style paired with their expressive approach combines factual precision with emotional engagement."
    }
    
    # Get the dynamics description or provide a default
    key = (user_style, other_style)
    return dynamics_map.get(key, "Your different communication styles may require some adaptation to understand each other effectively.")