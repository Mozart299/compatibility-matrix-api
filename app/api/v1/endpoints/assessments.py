# app/api/v1/endpoints/assessments.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Dict, Any, List, Optional
from supabase import Client
import logging
import traceback

from app.api.dependencies.auth import get_current_user
from app.db.supabase import get_supabase, get_admin_supabase

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("assessments_endpoint")

@router.get("")
async def get_assessments(
    request: Request,
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_admin_supabase)
):
    """Get all assessments for the current user"""
    try:
        # Log request information
        auth_header = request.headers.get("Authorization", "No Auth header")
        logger.info(f"GET /assessments request received")
        logger.info(f"Auth header present: {bool(auth_header)}")
        logger.info(f"Auth header prefix: {auth_header[:15]}..." if auth_header else "No Auth header")
        
        # Log user information from the token
        logger.info(f"User authenticated as: {current_user.id if current_user else 'No user'}")
        
        user_id = current_user.id
        logger.info(f"Fetching assessments for user_id: {user_id}")
        
        # Get user's assessment data from Supabase
        try:
            response = supabase.table('user_assessments') \
                .select('*, assessment_dimensions(*)') \
                .eq('user_id', user_id) \
                .execute()
            
            logger.info(f"user_assessments query executed successfully")
            logger.info(f"Response data length: {len(response.data) if response.data else 0}")
        except Exception as supabase_error:
            logger.error(f"Supabase query error: {str(supabase_error)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(supabase_error)}"
            )
        
        # Get list of all dimensions
        try:
            dimensions_response = supabase.table('assessment_dimensions') \
                .select('*') \
                .order('order_index') \
                .execute()
            
            logger.info(f"assessment_dimensions query executed successfully")
            logger.info(f"Dimensions data length: {len(dimensions_response.data) if dimensions_response.data else 0}")
            
            all_dimensions = dimensions_response.data
        except Exception as dimensions_error:
            logger.error(f"Dimensions query error: {str(dimensions_error)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching dimensions: {str(dimensions_error)}"
            )
        
        # Create a mapping of dimensions that have been started/completed
        assessment_map = {}
        for assessment in response.data:
            dimension_id = assessment['dimension_id']
            assessment_map[dimension_id] = {
                "id": assessment['id'],
                "status": assessment['status'],
                "progress": assessment['progress'],
                "responses": assessment['responses'],
                "created_at": assessment['created_at'],
                "updated_at": assessment['updated_at'],
                "dimension": assessment['assessment_dimensions']
            }
        
        # Create a complete assessment status list including dimensions not yet started
        assessments = []
        for dimension in all_dimensions:
            if dimension['id'] == 'biometric':
                continue
            if dimension['id'] in assessment_map:
                # Assessment exists for this dimension
                assessment_data = assessment_map[dimension['id']]
                assessments.append({
                    "id": assessment_data['id'],
                    "dimension_id": dimension['id'],
                    "dimension_name": dimension['name'],
                    "dimension_description": dimension['description'],
                    "status": assessment_data['status'],
                    "progress": assessment_data['progress'],
                    "created_at": assessment_data['created_at'],
                    "updated_at": assessment_data['updated_at']
                })
            else:
                # Assessment not started for this dimension
                assessments.append({
                    "dimension_id": dimension['id'],
                    "dimension_name": dimension['name'],
                    "dimension_description": dimension['description'],
                    "status": "not_started",
                    "progress": 0
                })
        
        # Calculate overall assessment progress
        total_dimensions = len(all_dimensions)
        completed_dimensions = sum(1 for a in assessments if a['status'] == 'completed')
        in_progress_dimensions = sum(1 for a in assessments if a['status'] == 'in_progress')
        
        overall_progress = 0
        if total_dimensions > 0:
            # Weight completed dimensions fully and in-progress dimensions by their progress percentage
            progress_sum = completed_dimensions * 100
            for assessment in assessments:
                if assessment['status'] == 'in_progress':
                    progress_sum += assessment['progress']
                    
            overall_progress = int(progress_sum / (total_dimensions * 100) * 100)
        
        logger.info(f"Successfully constructed response for user {user_id}")
        logger.info(f"Total dimensions: {total_dimensions}, Completed: {completed_dimensions}, In progress: {in_progress_dimensions}")
        
        return {
            "assessments": assessments,
            "overall_progress": overall_progress,
            "total_dimensions": total_dimensions,
            "completed_dimensions": completed_dimensions,
            "in_progress_dimensions": in_progress_dimensions
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_assessments: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching assessments: {str(e)}"
        )


@router.post("/start")
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
            assessment_id = existing.data[0]["id"]
            
            # Get dimension info
            dimension = supabase.table('assessment_dimensions') \
                .select('*') \
                .eq('id', dimension_id) \
                .execute()
                
            # Get questions for this dimension
            questions = supabase.table('assessment_questions') \
                .select('*') \
                .eq('dimension_id', dimension_id) \
                .order('order_index') \
                .execute()
                
            # Check if there are any responses already
            responses = existing.data[0].get("responses", [])
            
            # Get next unanswered question
            next_question_index = len(responses)
            next_question = None if next_question_index >= len(questions.data) else questions.data[next_question_index]
            
            return {
                "assessment_id": assessment_id,
                "status": existing.data[0]["status"],
                "progress": existing.data[0]["progress"],
                "dimension": dimension.data[0] if dimension.data else {},
                "total_questions": len(questions.data),
                "completed_questions": len(responses),
                "next_question": next_question,
                "message": "Assessment already started"
            }
            
        # Get dimension info
        dimension = supabase.table('assessment_dimensions') \
            .select('*') \
            .eq('id', dimension_id) \
            .execute()
            
        if not dimension.data or len(dimension.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dimension not found"
            )
            
        # Get questions for this dimension
        questions = supabase.table('assessment_questions') \
            .select('*') \
            .eq('dimension_id', dimension_id) \
            .order('order_index') \
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
            "dimension": dimension.data[0],
            "total_questions": len(questions.data),
            "completed_questions": 0,
            "next_question": questions.data[0] if questions.data else None,
            "message": "Assessment started successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting assessment: {str(e)}"
        )


@router.get("/dimensions")
async def get_assessment_dimensions(
    request: Request,
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Get all assessment dimensions"""
    try:
        # Log request information
        auth_header = request.headers.get("Authorization", "No Auth header")
        logger.info(f"GET /assessments/dimensions request received")
        logger.info(f"Auth header present: {bool(auth_header)}")
        logger.info(f"User authenticated as: {current_user.id if current_user else 'No user'}")
        
        try:
            # Get all assessment dimensions
            response = supabase.table('assessment_dimensions') \
                .select('*') \
                .order('order_index') \
                .execute()
            
            logger.info(f"Dimensions query successful, returned {len(response.data)} records")
                
            return {"dimensions": response.data}
        except Exception as db_error:
            logger.error(f"Database error in get_assessment_dimensions: {str(db_error)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching dimensions: {str(db_error)}"
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_assessment_dimensions: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dimensions: {str(e)}"
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
            .order('order_index') \
            .execute()
        
        # Get current responses
        responses = assessment.get("responses", [])
        
        # Determine next question
        next_question_index = len(responses)
        next_question = None if next_question_index >= len(questions.data) else questions.data[next_question_index]
        
        # For each answered question, add the response
        answered_questions = []
        for i, response_data in enumerate(responses):
            if i < len(questions.data):
                answered_questions.append({
                    **questions.data[i],
                    "response": response_data
                })
        
        return {
            "assessment": {
                "id": assessment["id"],
                "status": assessment["status"],
                "progress": assessment["progress"],
                "created_at": assessment["created_at"],
                "updated_at": assessment["updated_at"]
            },
            "dimension": dimension_info,
            "total_questions": len(questions.data),
            "completed_questions": len(responses),
            "next_question": next_question,
            "answered_questions": answered_questions,
            "remaining_questions": len(questions.data) - len(responses)
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
            # Get the current responses
            current_responses = current_assessment.get("responses", [])
            
            # Determine if we're adding a single response or multiple
            new_responses = assessment_data["responses"]
            if isinstance(new_responses, list):
                responses = current_responses + new_responses
            else:
                # Single response
                responses = current_responses + [new_responses]
            
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
                
            if not update_response.data or len(update_response.data) == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update assessment"
                )
                
            result = {
                "assessment": update_response.data[0],
                "progress": progress,
                "status": status,
                "total_questions": total_questions,
                "completed_questions": completed
            }
            
            # Add next question if not completed
            if status != "completed" and completed < total_questions:
                result["next_question"] = questions.data[completed]
                
            if status == "completed":
                # When an assessment is completed, recalculate compatibility scores
                await recalculate_compatibility_scores(user_id, current_assessment['dimension_id'], supabase)
                
                result["message"] = "Assessment completed successfully. Compatibility scores have been updated."
            else:
                result["message"] = "Assessment updated successfully"
            
            return result
            
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
            .order('order_index') \
            .execute()
            
        return {"questions": response.data}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching questions: {str(e)}"
        )

@router.post("/responses")
async def submit_response(
    response_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Submit a single response for an assessment question"""
    try:
        assessment_id = response_data.get("assessment_id")
        question_id = response_data.get("question_id")
        answer_value = response_data.get("value")
        
        if not assessment_id or not question_id or answer_value is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="assessment_id, question_id and value are required"
            )
            
        # Format the response
        response = {
            "question_id": question_id,
            "value": answer_value,
            "timestamp": 'now()'
        }
        
        # Update the assessment using the update endpoint
        result = await update_assessment(
            assessment_id=assessment_id,
            assessment_data={"responses": response},
            current_user=current_user,
            supabase=supabase
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting response: {str(e)}"
        )

@router.get("/progress")
async def get_assessment_progress(
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_admin_supabase)
):
    """Get overall assessment progress for the user"""
    try:
        # Use the get_assessments function to calculate overall progress
        assessment_data = await get_assessments(current_user, supabase)
        
        # Extract just the progress information
        return {
            "overall_progress": assessment_data["overall_progress"],
            "total_dimensions": assessment_data["total_dimensions"],
            "completed_dimensions": assessment_data["completed_dimensions"],
            "in_progress_dimensions": assessment_data["in_progress_dimensions"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating assessment progress: {str(e)}"
        )

async def recalculate_compatibility_scores(
    user_id: str,
    dimension_id: str,
    supabase: Client
):
    """
    Recalculate compatibility scores with other users based on completed assessment
    This is called after a user completes an assessment for a dimension
    """
    try:
        # Get all users who have completed this dimension's assessment
        completed_assessments = supabase.table('user_assessments') \
            .select('user_id, responses') \
            .eq('dimension_id', dimension_id) \
            .eq('status', 'completed') \
            .execute()
        
        # Get the current user's responses
        user_responses = next((a['responses'] for a in completed_assessments.data if a['user_id'] == user_id), None)
        
        if not user_responses:
            return  # No responses found, shouldn't happen
        
        # For each other user who has completed this dimension
        for other_assessment in completed_assessments.data:
            other_user_id = other_assessment['user_id']
            
            # Skip self-comparison
            if other_user_id == user_id:
                continue
                
            other_responses = other_assessment['responses']
            
            # Calculate compatibility score for this dimension
            dimension_score = calculate_compatibility_score(user_responses, other_responses)
            
            # Ensure user_id_a is always lexicographically less than user_id_b
            # This helps maintain the uniqueness constraint in the DB
            if user_id < other_user_id:
                user_id_a = user_id
                user_id_b = other_user_id
            else:
                user_id_a = other_user_id
                user_id_b = user_id
            
            # Check if there's an existing compatibility record
            existing_record = supabase.table('compatibility_scores') \
                .select('*') \
                .eq('user_id_a', user_id_a) \
                .eq('user_id_b', user_id_b) \
                .execute()
            
            # Prepare the dimension score data
            dimension_score_data = {
                "dimension_id": dimension_id,
                "score": dimension_score
            }
            
            if existing_record.data and len(existing_record.data) > 0:
                # Update existing record
                current_record = existing_record.data[0]
                dimension_scores = current_record.get('dimension_scores', [])
                
                # Check if this dimension already has a score
                dimension_index = next((i for i, d in enumerate(dimension_scores) if d.get('dimension_id') == dimension_id), -1)
                
                if dimension_index >= 0:
                    # Update existing dimension score
                    dimension_scores[dimension_index] = dimension_score_data
                else:
                    # Add new dimension score
                    dimension_scores.append(dimension_score_data)
                
                # Calculate overall score as average of dimension scores
                overall_score = int(sum(d['score'] for d in dimension_scores) / len(dimension_scores))
                
                # Update strengths and challenges based on dimension scores
                strengths, challenges = identify_strengths_and_challenges(dimension_scores)
                
                # Update the record
                supabase.table('compatibility_scores') \
                    .update({
                        'overall_score': overall_score,
                        'dimension_scores': dimension_scores,
                        'strengths': strengths,
                        'challenges': challenges,
                        'updated_at': 'now()'
                    }) \
                    .eq('id', current_record['id']) \
                    .execute()
            else:
                # Create new compatibility record
                supabase.table('compatibility_scores') \
                    .insert({
                        'user_id_a': user_id_a,
                        'user_id_b': user_id_b,
                        'overall_score': dimension_score,
                        'dimension_scores': [dimension_score_data],
                        'strengths': [],
                        'challenges': [],
                        'created_at': 'now()',
                        'updated_at': 'now()'
                    }) \
                    .execute()
                
    except Exception as e:
        print(f"Error recalculating compatibility scores: {str(e)}")
        # Don't raise here as this is called asynchronously
        # Just log the error and continue

def calculate_compatibility_score(user_responses, other_responses):
    """
    Calculate compatibility score between two sets of responses
    This is a simplified version - in production you'd implement
    the full algorithm from the compatibility conceptual framework
    """
    # Ensure the responses are comparable
    if len(user_responses) != len(other_responses):
        # If lengths differ, compare only the questions both users answered
        min_length = min(len(user_responses), len(other_responses))
        user_responses = user_responses[:min_length]
        other_responses = other_responses[:min_length]
    
    # Simple algorithm: compare answers and calculate similarity
    # 1. Exact matches get full points
    # 2. Close answers get partial points
    total_points = 0
    max_points = len(user_responses) * 100
    
    for i in range(len(user_responses)):
        user_value = user_responses[i].get('value')
        other_value = other_responses[i].get('value')
        
        # If response format is different, skip
        if not isinstance(user_value, type(other_value)):
            continue
            
        if isinstance(user_value, (int, float)):
            # Numeric values - closeness matters
            # Calculate similarity on a scale of 0-100
            difference = abs(user_value - other_value)
            max_difference = 4  # Assuming 5-point scale (1-5)
            similarity = max(0, 100 - (difference / max_difference) * 100)
            total_points += similarity
        elif user_value == other_value:
            # Exact match for non-numeric values
            total_points += 100
        else:
            # No match, no points
            pass
    
    # Calculate final score as percentage
    if max_points == 0:
        return 0
        
    return int(total_points / max_points * 100)

def identify_strengths_and_challenges(dimension_scores):
    """
    Identify relationship strengths and challenges based on dimension scores
    Returns two arrays: strengths and challenges
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