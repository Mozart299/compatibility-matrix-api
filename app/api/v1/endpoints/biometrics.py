# app/api/v1/endpoints/biometrics.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from supabase import Client
import math

from app.api.dependencies.auth import get_current_user
from app.db.supabase import get_supabase, get_admin_supabase

router = APIRouter()

@router.post("/hrv")
async def save_hrv_measurement(
    measurement_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_admin_supabase)
):
    """Save a new HRV measurement for the current user"""
    try:
        user_id = current_user.id
        
        # Validate the measurement data
        required_fields = ["sdnn", "rmssd", "lf_hf_ratio", "hrvScore"]
        for field in required_fields:
            if field not in measurement_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Create measurement record
        measurement = {
            "user_id": user_id,
            "measurement_type": "hrv",
            "measurement_value": {
                "sdnn": measurement_data["sdnn"],
                "rmssd": measurement_data["rmssd"],
                "lf_hf_ratio": measurement_data["lf_hf_ratio"],
                "hrv_score": measurement_data["hrvScore"]
            },
            "created_at": 'now()',
            "updated_at": 'now()'
        }
        
        # Insert into biometric_measurements table
        measurement_response = supabase.table('biometric_measurements') \
            .insert(measurement) \
            .execute()
        
        if not measurement_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save measurement"
            )
        
        # After saving the measurement, recalculate compatibility scores with other users
        # This would typically be done in a background job for better performance
        await recalculate_biometric_compatibility(user_id, supabase)
        
        return {
            "success": True,
            "message": "HRV measurement saved successfully",
            "measurement_id": measurement_response.data[0]["id"],
            "measurement": measurement_response.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving HRV measurement: {str(e)}"
        )

@router.get("/hrv")
async def get_hrv_measurements(
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
    limit: int = 10
):
    """Get the most recent HRV measurements for the current user"""
    try:
        user_id = current_user.id
        
        # Query biometric_measurements table for HRV measurements
        response = supabase.table('biometric_measurements') \
            .select('*') \
            .eq('user_id', user_id) \
            .eq('measurement_type', 'hrv') \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()
        
        return {
            "measurements": response.data,
            "count": len(response.data)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching HRV measurements: {str(e)}"
        )

@router.get("/compatibility/{user_id}")
async def get_biometric_compatibility(
    user_id: str,
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Get biometric compatibility with another user"""
    try:
        current_user_id = current_user.id
        
        # Ensure specified user exists
        user_check = supabase.table('profiles') \
            .select('id') \
            .eq('id', user_id) \
            .execute()
            
        if not user_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        # Determine the correct order for user IDs (user_id_a should always be lexicographically less than user_id_b)
        if current_user_id < user_id:
            user_id_a = current_user_id
            user_id_b = user_id
        else:
            user_id_a = user_id
            user_id_b = current_user_id
            
        # Check if compatibility record exists
        compatibility = supabase.table('biometric_compatibility_scores') \
            .select('*') \
            .eq('user_id_a', user_id_a) \
            .eq('user_id_b', user_id_b) \
            .eq('biometric_type', 'hrv') \
            .execute()
            
        if compatibility.data:
            return compatibility.data[0]
            
        # If no compatibility record exists, check if both users have HRV measurements
        current_user_hrv = supabase.table('biometric_measurements') \
            .select('*') \
            .eq('user_id', current_user_id) \
            .eq('measurement_type', 'hrv') \
            .order('created_at', desc=True) \
            .limit(1) \
            .execute()
            
        other_user_hrv = supabase.table('biometric_measurements') \
            .select('*') \
            .eq('user_id', user_id) \
            .eq('measurement_type', 'hrv') \
            .order('created_at', desc=True) \
            .limit(1) \
            .execute()
            
        if not current_user_hrv.data or not other_user_hrv.data:
            return {
                "user_id_a": user_id_a,
                "user_id_b": user_id_b,
                "biometric_type": "hrv",
                "compatibility_score": None,
                "compatibility_details": None,
                "message": "One or both users have not completed HRV measurements yet"
            }
            
        # Calculate compatibility if both measurements exist but record doesn't
        compatibility_score, details = calculate_hrv_compatibility(
            current_user_hrv.data[0]["measurement_value"],
            other_user_hrv.data[0]["measurement_value"]
        )
        
        # Create and return a compatibility record without saving it
        return {
            "user_id_a": user_id_a,
            "user_id_b": user_id_b,
            "biometric_type": "hrv",
            "compatibility_score": compatibility_score,
            "compatibility_details": details,
            "created_at": None,
            "message": "Compatibility calculated but not yet saved"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching biometric compatibility: {str(e)}"
        )

async def recalculate_biometric_compatibility(
    user_id: str,
    supabase: Client
):
    """Recalculate biometric compatibility with all other users who have HRV measurements"""
    try:
        # Get the user's most recent HRV measurement
        user_hrv = supabase.table('biometric_measurements') \
            .select('*') \
            .eq('user_id', user_id) \
            .eq('measurement_type', 'hrv') \
            .order('created_at', desc=True) \
            .limit(1) \
            .execute()
            
        if not user_hrv.data:
            return  # No HRV data available
            
        user_measurement = user_hrv.data[0]["measurement_value"]
        
        # Get all other users with HRV measurements
        other_users = supabase.table('biometric_measurements') \
            .select('user_id, measurement_value, created_at') \
            .eq('measurement_type', 'hrv') \
            .neq('user_id', user_id) \
            .execute()
            
        # Get unique user IDs - only the most recent measurement per user
        user_dict = {}
        for item in other_users.data:
            if item["user_id"] not in user_dict or item["created_at"] > user_dict[item["user_id"]]["created_at"]:
                user_dict[item["user_id"]] = item
                
        # Calculate compatibility with each user and update/create records
        for other_user_id, other_user_data in user_dict.items():
            # Determine the correct order for user IDs
            if user_id < other_user_id:
                user_id_a = user_id
                user_id_b = other_user_id
            else:
                user_id_a = other_user_id
                user_id_b = user_id
                
            # Calculate compatibility score
            compatibility_score, details = calculate_hrv_compatibility(
                user_measurement,
                other_user_data["measurement_value"]
            )
            
            # Check if compatibility record exists
            existing_record = supabase.table('biometric_compatibility_scores') \
                .select('id') \
                .eq('user_id_a', user_id_a) \
                .eq('user_id_b', user_id_b) \
                .eq('biometric_type', 'hrv') \
                .execute()
                
            if existing_record.data:
                # Update existing record
                supabase.table('biometric_compatibility_scores') \
                    .update({
                        'compatibility_score': compatibility_score,
                        'compatibility_details': details,
                        'updated_at': 'now()'
                    }) \
                    .eq('id', existing_record.data[0]["id"]) \
                    .execute()
            else:
                # Create new record
                supabase.table('biometric_compatibility_scores') \
                    .insert({
                        'user_id_a': user_id_a,
                        'user_id_b': user_id_b,
                        'biometric_type': 'hrv',
                        'compatibility_score': compatibility_score,
                        'compatibility_details': details,
                        'created_at': 'now()',
                        'updated_at': 'now()'
                    }) \
                    .execute()
                    
        # Update the general compatibility scores to include biometric dimension
        await update_overall_compatibility_scores(user_id, supabase)
                
    except Exception as e:
        print(f"Error in recalculate_biometric_compatibility: {str(e)}")
        # Log the error but don't raise exception as this is a background operation

def calculate_hrv_compatibility(
    user1_hrv: Dict[str, Any],
    user2_hrv: Dict[str, Any]
) -> tuple[int, Dict[str, Any]]:
    """
    Calculate compatibility between two users' HRV measurements
    
    The algorithm considers:
    1. SDNN Complementarity (40%)
    2. LF/HF Ratio Compatibility (40%)
    3. Overall HRV Score similarity (20%)
    """
    # Extract HRV metrics
    user1_sdnn = user1_hrv.get("sdnn", 0)
    user2_sdnn = user2_hrv.get("sdnn", 0)
    
    user1_lf_hf = user1_hrv.get("lf_hf_ratio", 1.0)
    user2_lf_hf = user2_hrv.get("lf_hf_ratio", 1.0)
    
    user1_score = user1_hrv.get("hrv_score", 0)
    user2_score = user2_hrv.get("hrv_score", 0)
    
    # Calculate SDNN complementarity (40%)
    # Higher scores if both have high SDNN (good) or if one has high and one has moderate (complementary)
    max_sdnn = max(user1_sdnn, user2_sdnn)
    min_sdnn = min(user1_sdnn, user2_sdnn)
    
    sdnn_ratio = min_sdnn / max_sdnn if max_sdnn > 0 else 0
    
    # Higher scores when both are above 50 or when there's a good balance
    if min_sdnn >= 50:
        # Both have good SDNN - similarity bonus
        sdnn_score = 100 * sdnn_ratio
    else:
        # One higher, one lower - complementarity check
        sdnn_diff = abs(user1_sdnn - user2_sdnn)
        # Optimal difference around 20-30ms
        if 15 <= sdnn_diff <= 40:
            sdnn_score = 90  # Complementary values
        else:
            # Less ideal but still somewhat compatible
            sdnn_score = max(50, 100 - (abs(sdnn_diff - 25) * 1.5))
    
    # Calculate LF/HF ratio compatibility (40%)
    # Ideal: one partner has higher parasympathetic dominance (lower LF/HF) to balance other's sympathetic state
    lf_hf_diff = abs(user1_lf_hf - user2_lf_hf)
    
    # Optimal LF/HF difference around 0.5-1.0 (complementary)
    if 0.5 <= lf_hf_diff <= 1.0:
        lf_hf_score = 100  # Ideal complementary balance
    else:
        # Less ideal but still somewhat compatible
        lf_hf_score = max(50, 100 - (abs(lf_hf_diff - 0.75) * 40))
    
    # Calculate overall HRV score similarity (20%)
    # Higher scores have better adaptability and can work with more partners
    hrv_score_diff = abs(user1_score - user2_score)
    
    if max(user1_score, user2_score) >= 80:
        # If one person has excellent HRV, they're generally compatible with anyone
        hrv_score_comp = 90
    elif hrv_score_diff <= 15:
        # Similar HRV scores - good compatibility
        hrv_score_comp = 100
    else:
        # Less similar scores
        hrv_score_comp = max(50, 100 - (hrv_score_diff - 15) * 2)
    
    # Calculate final weighted compatibility score
    final_score = int((sdnn_score * 0.4) + (lf_hf_score * 0.4) + (hrv_score_comp * 0.2))
    
    # Create detailed compatibility breakdown
    details = {
        "sdnn_compatibility": {
            "score": round(sdnn_score),
            "user1_value": user1_sdnn,
            "user2_value": user2_sdnn,
            "description": get_sdnn_compatibility_description(user1_sdnn, user2_sdnn)
        },
        "lf_hf_compatibility": {
            "score": round(lf_hf_score),
            "user1_value": user1_lf_hf,
            "user2_value": user2_lf_hf,
            "description": get_lf_hf_compatibility_description(user1_lf_hf, user2_lf_hf)
        },
        "hrv_score_compatibility": {
            "score": round(hrv_score_comp),
            "user1_value": user1_score,
            "user2_value": user2_score,
            "description": get_hrv_score_compatibility_description(user1_score, user2_score)
        }
    }
    
    return final_score, details

def get_sdnn_compatibility_description(sdnn1: float, sdnn2: float) -> str:
    """Get description of SDNN compatibility"""
    max_sdnn = max(sdnn1, sdnn2)
    min_sdnn = min(sdnn1, sdnn2)
    diff = abs(sdnn1 - sdnn2)
    
    if min_sdnn >= 60:
        return "Both partners show excellent autonomic flexibility, suggesting a relationship with strong stress resilience."
    elif min_sdnn >= 40 and max_sdnn >= 60:
        return "The balance between your autonomic flexibility patterns suggests good emotional co-regulation potential."
    elif 15 <= diff <= 40:
        return "Your complementary autonomic patterns may help balance each other's stress responses."
    else:
        return "Your autonomic patterns suggest you may respond similarly to stress, which can be both a strength and challenge."

def get_lf_hf_compatibility_description(lf_hf1: float, lf_hf2: float) -> str:
    """Get description of LF/HF ratio compatibility"""
    diff = abs(lf_hf1 - lf_hf2)
    
    if 0.5 <= diff <= 1.0:
        return "Your complementary autonomic balance patterns suggest one partner may help calm the other during stress."
    elif diff < 0.3:
        return "Your similar autonomic balance patterns suggest you may respond to stress in similar ways."
    else:
        return "Your autonomic balance patterns show moderate complementarity for stress response synchronization."

def get_hrv_score_compatibility_description(score1: int, score2: int) -> str:
    """Get description of overall HRV score compatibility"""
    max_score = max(score1, score2)
    diff = abs(score1 - score2)
    
    if max_score >= 80:
        return "At least one partner has excellent autonomic regulation, potentially stabilizing the relationship during stress."
    elif diff <= 15:
        return "Your similar overall autonomic profiles suggest synchronized emotional responses."
    else:
        return "Your different autonomic profiles may offer balanced perspectives during emotional situations."

async def update_overall_compatibility_scores(user_id: str, supabase: Client):
    """Update overall compatibility scores to include biometric dimension"""
    try:
        print(f"Starting update of overall compatibility scores for user {user_id}")
        
        # Get all biometric compatibility scores for this user
        biometric_scores = supabase.table('biometric_compatibility_scores') \
            .select('*') \
            .or_(f'user_id_a.eq.{user_id},user_id_b.eq.{user_id}') \
            .eq('biometric_type', 'hrv') \
            .execute()
            
        if not biometric_scores.data:
            print(f"No biometric scores found for user {user_id}")
            return  # No biometric scores to integrate
            
        print(f"Found {len(biometric_scores.data)} biometric scores for user {user_id}")
            
        # For each biometric score, update the corresponding overall compatibility
        for bio_score in biometric_scores.data:
            other_user_id = bio_score['user_id_a'] if bio_score['user_id_a'] != user_id else bio_score['user_id_b']
            
            print(f"Processing biometric compatibility between {user_id} and {other_user_id}")
            
            # Determine the correct order for user IDs in compatibility_scores table
            user_id_a = min(user_id, other_user_id)
            user_id_b = max(user_id, other_user_id)
            
            # Check if overall compatibility exists
            compatibility = supabase.table('compatibility_scores') \
                .select('*') \
                .eq('user_id_a', user_id_a) \
                .eq('user_id_b', user_id_b) \
                .execute()
                
            if not compatibility.data:
                print(f"No compatibility record found between {user_id_a} and {user_id_b}")
                # Instead of skipping, create a basic compatibility record with just biometric data
                biometric_dimension = {
                    "dimension_id": "9fdf8cff-974b-4ffe-913d-5e0eb0dc48c9",
                    "name": "Physiological Compatibility",
                    "score": bio_score['compatibility_score']
                }
                
                new_record = {
                    "user_id_a": user_id_a,
                    "user_id_b": user_id_b,
                    "overall_score": bio_score['compatibility_score'],
                    "dimension_scores": [biometric_dimension],
                    "strengths": [{
                        "dimension_id": "9fdf8cff-974b-4ffe-913d-5e0eb0dc48c9",
                        "score": bio_score['compatibility_score']
                    }] if bio_score['compatibility_score'] >= 70 else [],
                    "challenges": [{
                        "dimension_id": "9fdf8cff-974b-4ffe-913d-5e0eb0dc48c9",
                        "score": bio_score['compatibility_score']
                    }] if bio_score['compatibility_score'] < 50 else [],
                    "created_at": 'now()',
                    "updated_at": 'now()'
                }
                
                try:
                    supabase.table('compatibility_scores').insert(new_record).execute()
                    print(f"Created new compatibility record between {user_id_a} and {user_id_b}")
                except Exception as insert_err:
                    print(f"Error creating new compatibility record: {str(insert_err)}")
                
                continue
                
            # Get current compatibility record
            compat_record = compatibility.data[0]
            current_dimensions = compat_record.get('dimension_scores', [])
            
            # Check if biometric dimension already exists
            biometric_index = next((i for i, d in enumerate(current_dimensions) 
                                    if d.get('dimension_id') == '9fdf8cff-974b-4ffe-913d-5e0eb0dc48c9'), -1)
            
            biometric_dimension = {
                "dimension_id": "9fdf8cff-974b-4ffe-913d-5e0eb0dc48c9",
                "name": "Physiological Compatibility",
                "score": bio_score['compatibility_score']
            }
            
            # Update or add biometric dimension
            if biometric_index >= 0:
                current_dimensions[biometric_index] = biometric_dimension
                print(f"Updated biometric dimension for users {user_id_a} and {user_id_b}")
            else:
                current_dimensions.append(biometric_dimension)
                print(f"Added new biometric dimension for users {user_id_a} and {user_id_b}")
                
            # Recalculate overall score as average of dimension scores
            overall_score = int(sum(d.get('score', 0) for d in current_dimensions) / len(current_dimensions))
            
            # Update strengths and challenges based on dimension scores
            strengths, challenges = identify_strengths_and_challenges(current_dimensions)
            
            # Update the compatibility record
            try:
                update_response = supabase.table('compatibility_scores') \
                    .update({
                        'overall_score': overall_score,
                        'dimension_scores': current_dimensions,
                        'strengths': strengths,
                        'challenges': challenges,
                        'updated_at': 'now()'
                    }) \
                    .eq('id', compat_record['id']) \
                    .execute()
                    
                print(f"Updated compatibility record between {user_id_a} and {user_id_b}")
                print(f"New overall score: {overall_score}")
            except Exception as update_err:
                print(f"Error updating compatibility record: {str(update_err)}")
                
    except Exception as e:
        print(f"Error in update_overall_compatibility_scores: {str(e)}")
        # Log the error but don't raise exception as this is a background operation


def identify_strengths_and_challenges(dimension_scores: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Identify relationship strengths and challenges based on dimension scores
    This function is copied from assessments.py to maintain consistency
    """
    # Sort dimensions by score
    sorted_dimensions = sorted(dimension_scores, key=lambda d: d['score'], reverse=True)
    
    # Top 3 dimensions are strengths
    strengths = []
    for dimension in sorted_dimensions[:3]:
        if dimension['score'] >= 70:  # Only high scores qualify as strengths
            strengths.append({
                "dimension_id": dimension['dimension_id'],
                "score": dimension['score']
            })
    
    # Bottom 2 dimensions are challenges
    challenges = []
    reversed_dimensions = sorted_dimensions[::-1]
    for dimension in reversed_dimensions[:2]:
        if dimension['score'] < 70:  # Only lower scores qualify as challenges
            challenges.append({
                "dimension_id": dimension['dimension_id'],
                "score": dimension['score']
            })
    
    return strengths, challenges