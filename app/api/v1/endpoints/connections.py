# app/api/v1/endpoints/connections.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
from supabase import Client
from fastapi import Depends, HTTPException, status, Header

from app.api.dependencies.auth import get_current_user
from app.db.supabase import get_supabase, get_admin_supabase

router = APIRouter()

@router.get("")
async def get_connections(
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_admin_supabase),
    status: Optional[str] = None
):
    """
    Get all connections for the current user
    
    Optional query parameter:
    - status: Filter by connection status ('pending', 'accepted', 'declined')
    """
    try:
        user_id = current_user.id
        
        # Build query based on connection status (if provided)
        query = supabase.table('connections') \
            .select('id, user_id_sender, user_id_receiver, status, created_at, updated_at') \
            .or_(f'user_id_sender.eq.{user_id},user_id_receiver.eq.{user_id}')
            
        if status:
            query = query.eq('status', status)
            
        response = query.execute()
        
        if not response.data:
            return {"connections": []}
        
        # Get all unique user IDs from connections
        user_ids = set()
        for connection in response.data:
            user_ids.add(connection['user_id_sender'])
            user_ids.add(connection['user_id_receiver'])
        
        # Remove current user from the list
        user_ids.discard(user_id)
        
        # Fetch user profiles
        profiles_response = supabase.table('profiles') \
            .select('id, name, avatar_url') \
            .in_('id', list(user_ids)) \
            .execute()
            
        # Create a mapping of user IDs to profiles
        profiles_map = {profile['id']: profile for profile in profiles_response.data}
        
        # Prepare the connections data for response
        connections = []
        for conn in response.data:
            # Determine which user is the other user in the connection
            other_user_id = conn['user_id_receiver'] if conn['user_id_sender'] == user_id else conn['user_id_sender']
            
            # Get that user's profile
            other_user = profiles_map.get(other_user_id, {'name': 'Unknown User', 'avatar_url': None})
            
            # Determine the direction of the connection request
            direction = "outgoing" if conn['user_id_sender'] == user_id else "incoming"
            
            # Fetch compatibility data if connection is accepted
            compatibility_score = None
            if conn['status'] == 'accepted':
                # Ensure user_id_a is always lexicographically less than user_id_b
                # to match the constraint in the compatibility_scores table
                user_id_a = user_id if user_id < other_user_id else other_user_id
                user_id_b = other_user_id if user_id < other_user_id else user_id
                
                compatibility_response = supabase.table('compatibility_scores') \
                    .select('overall_score, strengths, challenges, dimension_scores') \
                    .eq('user_id_a', user_id_a) \
                    .eq('user_id_b', user_id_b) \
                    .execute()
                    
                if compatibility_response.data:
                    compatibility_score = compatibility_response.data[0]
            
            connections.append({
                "id": conn['id'],
                "user_id": other_user_id,
                "name": other_user['name'],
                "avatar_url": other_user.get('avatar_url'),
                "status": conn['status'],
                "direction": direction,
                "created_at": conn['created_at'],
                "updated_at": conn['updated_at'],
                "compatibility": compatibility_score
            })
        
        return {"connections": connections}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching connections: {str(e)}"
        )

@router.post("/request")
async def send_connection_request(
    request_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    authorization: Optional[str] = Header(None),
    supabase: Client = Depends(get_admin_supabase)
):
    """Send a connection request to another user"""
    try:
        user_id = current_user.id
        receiver_id = request_data.get("user_id")
        
        if not receiver_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id is required"
            )
            
        # Prevent sending request to self
        if user_id == receiver_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot send connection request to yourself"
            )
            
        # Check if the user exists
        user_response = supabase.table('profiles') \
            .select('id') \
            .eq('id', receiver_id) \
            .execute()
            
        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        # Check if a connection already exists
        existing_connection = supabase.table('connections') \
            .select('id, status, user_id_sender, user_id_receiver') \
            .or_(f'user_id_sender.eq.{user_id},user_id_receiver.eq.{user_id}') \
            .in_('user_id_receiver', [receiver_id]) \
            .in_('user_id_sender', [receiver_id]) \
            .execute()
            
        if existing_connection.data:
            conn = existing_connection.data[0]
            status_msg = "pending" if conn['status'] == 'pending' else "established"
            
            return {
                "success": False,
                "message": f"A connection is already {status_msg} between these users",
                "connection_id": conn['id'],
                "status": conn['status']
            }
            
        # Create a new connection request
        new_connection = {
            "user_id_sender": user_id,
            "user_id_receiver": receiver_id,
            "initiated_by": user_id,
            "status": "pending",
            "created_at": 'now()',
            "updated_at": 'now()'
        }
        
        response = supabase.table('connections').insert(new_connection).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create connection request"
            )
            
        return {
            "success": True,
            "message": "Connection request sent successfully",
            "connection_id": response.data[0]['id'],
            "status": "pending"
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending connection request: {str(e)}"
        )

@router.post("/{connection_id}/respond")
async def respond_to_connection_request(
    connection_id: str,
    response_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Respond to a connection request (accept or decline)"""
    try:
        user_id = current_user.id
        action = response_data.get("action")
        
        if action not in ["accept", "decline"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action must be either 'accept' or 'decline'"
            )
            
        # Get the connection and ensure it's pending and the current user is the receiver
        connection_response = supabase.table('connections') \
            .select('id, user_id_sender, user_id_receiver, status') \
            .eq('id', connection_id) \
            .eq('user_id_receiver', user_id) \
            .eq('status', 'pending') \
            .execute()
            
        if not connection_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection request not found, not pending, or you're not the receiver"
            )
            
        connection = connection_response.data[0]
        
        # Update the connection status based on the action
        update_data = {
            "status": "accepted" if action == "accept" else "declined",
            "updated_at": 'now()'
        }
        
        update_response = supabase.table('connections') \
            .update(update_data) \
            .eq('id', connection_id) \
            .execute()
            
        if not update_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update connection"
            )
            
        # If accepted, trigger compatibility calculation
        if action == "accept":
            sender_id = connection['user_id_sender']
            
            # In a real implementation, this would be a background job
            # For this MVP, we'll just update any existing compatibility data or create it if needed
            try:
                # Ensure user_id_a is lexicographically less than user_id_b (database constraint)
                user_id_a = user_id if user_id < sender_id else sender_id
                user_id_b = sender_id if user_id < sender_id else user_id
                
                # Check for existing compatibility data
                compatibility_exists = supabase.table('compatibility_scores') \
                    .select('id') \
                    .eq('user_id_a', user_id_a) \
                    .eq('user_id_b', user_id_b) \
                    .execute()
                
                # If no compatibility data exists, we need to create initial data
                # In a real app, we would calculate real compatibility based on assessments
                if not compatibility_exists.data:
                    # Create a basic entry with placeholder scores
                    compatibility_data = {
                        'user_id_a': user_id_a,
                        'user_id_b': user_id_b,
                        'overall_score': 70,  # Placeholder score
                        'dimension_scores': [
                            {'dimension_id': 'personality', 'name': 'Personality Traits', 'score': 75},
                            {'dimension_id': 'values', 'name': 'Values & Beliefs', 'score': 68},
                            {'dimension_id': 'interests', 'name': 'Interests', 'score': 72}
                        ],
                        'created_at': 'now()',
                        'updated_at': 'now()'
                    }
                    
                    supabase.table('compatibility_scores').insert(compatibility_data).execute()
            except Exception as calc_err:
                # Don't fail the request if compatibility calculation fails
                print(f"Error calculating compatibility: {str(calc_err)}")
            
            return {
                "success": True,
                "message": "Connection request accepted",
                "connection": update_response.data[0]
            }
        else:
            return {
                "success": True,
                "message": "Connection request declined",
                "connection": update_response.data[0]
            }
            
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error responding to connection request: {str(e)}"
        )

@router.delete("/{connection_id}")
async def remove_connection(
    connection_id: str,
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Remove a connection or cancel a request"""
    try:
        user_id = current_user.id
        
        # Get the connection and ensure the current user is part of it
        connection_response = supabase.table('connections') \
            .select('id, user_id_sender, user_id_receiver, status') \
            .eq('id', connection_id) \
            .or_(f'user_id_sender.eq.{user_id},user_id_receiver.eq.{user_id}') \
            .execute()
            
        if not connection_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
            
        connection = connection_response.data[0]
        
        # Delete the connection
        delete_response = supabase.table('connections') \
            .delete() \
            .eq('id', connection_id) \
            .execute()
        
        # Determine appropriate message based on connection status and role
        is_sender = connection['user_id_sender'] == user_id
        status_message = connection['status']
        
        if status_message == 'pending':
            message = "Connection request canceled" if is_sender else "Connection request declined"
        else:
            message = "Connection removed successfully"
            
        return {
            "success": True,
            "message": message
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing connection: {str(e)}"
        )

@router.get("/suggested")
async def get_suggested_connections(
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
    limit: int = Query(10, ge=1, le=50),
    min_score: Optional[int] = Query(None, ge=0, le=100)
):
    """Get suggested connections based on compatibility scores"""
    try:
        user_id = current_user.id
        
        # Get users with completed assessments (potential connections)
        users_response = supabase.table('user_assessments') \
            .select('user_id') \
            .eq('status', 'completed') \
            .neq('user_id', user_id) \
            .execute()
            
        if not users_response.data:
            return {"suggestions": []}
            
        # Get unique user IDs
        potential_user_ids = set(item['user_id'] for item in users_response.data)
        
        # Get existing connections to exclude them
        connections_response = supabase.table('connections') \
            .select('user_id_sender, user_id_receiver, status') \
            .or_(f'user_id_sender.eq.{user_id},user_id_receiver.eq.{user_id}') \
            .execute()
            
        # Extract the other user IDs from connections and their status
        connected_user_ids = set()
        pending_user_ids = set()
        
        for conn in connections_response.data:
            other_id = conn['user_id_receiver'] if conn['user_id_sender'] == user_id else conn['user_id_sender']
            
            if conn['status'] == 'pending':
                pending_user_ids.add(other_id)
            else:
                connected_user_ids.add(other_id)
                
        # Filter out already connected users
        available_user_ids = potential_user_ids - connected_user_ids
        
        if not available_user_ids:
            return {"suggestions": []}
            
        # Get suggestions
        suggestions = []
        
        # Get profiles for these users
        profiles_response = supabase.table('profiles') \
            .select('id, name, avatar_url') \
            .in_('id', list(available_user_ids)) \
            .execute()
            
        # Create a mapping of user IDs to profiles
        profiles_map = {profile['id']: profile for profile in profiles_response.data}
        
        # For each potential user, check compatibility
        for other_user_id in available_user_ids:
            # Ensure user_id_a is always lexicographically less than user_id_b
            user_id_a = user_id if user_id < other_user_id else other_user_id
            user_id_b = other_user_id if user_id < other_user_id else user_id
            
            compatibility_response = supabase.table('compatibility_scores') \
                .select('overall_score, strengths, challenges, dimension_scores') \
                .eq('user_id_a', user_id_a) \
                .eq('user_id_b', user_id_b) \
                .execute()
                
            # If no compatibility data, or score is below minimum, skip
            if not compatibility_response.data:
                continue
                
            compatibility = compatibility_response.data[0]
            
            if min_score is not None and compatibility['overall_score'] < min_score:
                continue
                
            # Get profile data for this user
            profile = profiles_map.get(other_user_id, {'name': 'Unknown User', 'avatar_url': None})
            
            # Add pending status flag if the user has a pending request
            pending = other_user_id in pending_user_ids
            
            suggestions.append({
                "user_id": other_user_id,
                "name": profile['name'],
                "avatar_url": profile.get('avatar_url'),
                "compatibility": compatibility,
                "has_pending_request": pending
            })
        
        # Sort by compatibility score (highest first) and limit results
        suggestions.sort(key=lambda x: x['compatibility']['overall_score'], reverse=True)
        suggestions = suggestions[:limit]
        
        return {"suggestions": suggestions}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting suggested connections: {str(e)}"
        )