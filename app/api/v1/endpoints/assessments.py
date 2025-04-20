# app/api/v1/endpoints/assessments.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from supabase import Client

from app.api.dependencies.auth import get_current_user
from app.db.supabase import get_supabase

router = APIRouter()

@router.get("/")
async def get_assessments(
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Get all assessments for the current user"""
    try:
        user_id = current_user.id
        
        # Get user's assessment data from Supabase
        response = supabase.table('user_assessments') \
            .select('*') \
            .eq('user_id', user_id) \
            .execute()
            
        return {"assessments": response.data}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching assessments: {str(e)}"
        )

@router.post("/")
async def start_assessment(
    assessment_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Start a new assessment or continue an existing one"""
    try:
        user_id = current_user.id
        dimension_id = assessment_data.get("dimension_id")
        
        if not dimension_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="dimension_id is required"
            )
            
        # Check if this assessment already exists
        existing = supabase.table('user_assessments') \
            .select('*') \
            .eq('user_id', user_id) \
            .eq('dimension_id', dimension_id) \
            .execute()
            
        if existing.data and len(existing.data) > 0:
            # Assessment exists, return current state
            return {
                "assessment_id": existing.data[0]["id"],
                "status": existing.data[0]["status"],
                "progress": existing.data[0]["progress"],
                "message": "Assessment already started"
            }
            
        # Get questions for this dimension
        questions = supabase.table('assessment_questions') \
            .select('*') \
            .eq('dimension_id', dimension_id) \
            .execute()
            
        if not questions.data or len(questions.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No questions found for this dimension"
            )
            
        # Create new assessment
        new_assessment = {
            "user_id": user_id,
            "dimension_id": dimension_id,
            "status": "in_progress",
            "progress": 0,
            "responses": [],  # Empty array to store responses
            "created_at": 'now()',
            "updated_at": 'now()'
        }
        
        # Insert new assessment into Supabase
        response = supabase.table('user_assessments').insert(new_assessment).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create assessment"
            )
            
        return {
            "assessment_id": response.data[0]["id"],
            "status": "in_progress",
            "progress": 0,
            "question_count": len(questions.data),
            "message": "Assessment started successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting assessment: {str(e)}"
        )

@router.get("/{assessment_id}")
async def get_assessment(
    assessment_id: str,
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Get details of a specific assessment"""
    try:
        user_id = current_user.id
        
        # Get assessment from Supabase
        response = supabase.table('user_assessments') \
            .select('*') \
            .eq('id', assessment_id) \
            .eq('user_id', user_id) \
            .execute()
            
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found"
            )
            
        assessment = response.data[0]
        
        # Get dimension info
        dimension = supabase.table('assessment_dimensions') \
            .select('*') \
            .eq('id', assessment['dimension_id']) \
            .execute()
        
        dimension_info = dimension.data[0] if dimension.data else {}
        
        # Get questions
        questions = supabase.table('assessment_questions') \
            .select('*') \
            .eq('dimension_id', assessment['dimension_id']) \
            .execute()
            
        return {
            "assessment": assessment,
            "dimension": dimension_info,
            "questions": questions.data,
            "total_questions": len(questions.data),
            "completed_questions": len(assessment.get("responses", [])),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching assessment: {str(e)}"
        )

@router.put("/{assessment_id}")
async def update_assessment(
    assessment_id: str,
    assessment_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Update an assessment with new responses"""
    try:
        user_id = current_user.id
        
        # Validate that this assessment belongs to the user
        response = supabase.table('user_assessments') \
            .select('*') \
            .eq('id', assessment_id) \
            .eq('user_id', user_id) \
            .execute()
            
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found"
            )
            
        current_assessment = response.data[0]
        
        # Process new responses
        if "responses" in assessment_data:
            responses = current_assessment.get("responses", []) + assessment_data["responses"]
            
            # Get total questions for this dimension
            questions = supabase.table('assessment_questions') \
                .select('*') \
                .eq('dimension_id', current_assessment['dimension_id']) \
                .execute()
                
            total_questions = len(questions.data)
            completed = len(responses)
            progress = int((completed / total_questions) * 100) if total_questions > 0 else 0
            
            # Check if assessment is complete
            status = "completed" if progress >= 100 else "in_progress"
            
            # Update assessment in Supabase
            update_data = {
                "responses": responses,
                "progress": progress,
                "status": status,
                "updated_at": 'now()'
            }
            
            update_response = supabase.table('user_assessments') \
                .update(update_data) \
                .eq('id', assessment_id) \
                .execute()
                
            if status == "completed":
                # When an assessment is completed, we would potentially
                # recalculate compatibility scores with other users
                # This would be a more complex operation handled by a background process
                # For now, we'll just return a message
                return {
                    "assessment": update_response.data[0],
                    "progress": progress,
                    "status": status,
                    "message": "Assessment completed successfully. Compatibility scores will be updated."
                }
            
            return {
                "assessment": update_response.data[0],
                "progress": progress,
                "status": status,
                "message": "Assessment updated successfully"
            }
            
        return {"message": "No changes made to assessment"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating assessment: {str(e)}"
        )

@router.get("/questions/{dimension_id}")
async def get_questions(
    dimension_id: str,
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Get questions for a specific assessment dimension"""
    try:
        # Get questions from Supabase
        response = supabase.table('assessment_questions') \
            .select('*') \
            .eq('dimension_id', dimension_id) \
            .execute()
            
        return {"questions": response.data}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching questions: {str(e)}"
        )

@router.post("/responses")
async def submit_responses(
    response_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Submit responses for an assessment"""
    try:
        assessment_id = response_data.get("assessment_id")
        responses = response_data.get("responses", [])
        
        if not assessment_id or not responses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="assessment_id and responses are required"
            )
            
        # Update the assessment using the update endpoint
        result = await update_assessment(
            assessment_id=assessment_id,
            assessment_data={"responses": responses},
            current_user=current_user,
            supabase=supabase
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting responses: {str(e)}"
        )