from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import logging
from datetime import datetime

# Import authentication and database
from routes.auth import get_current_user
from db.connection import execute_query, execute_query_one

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class SessionCreate(BaseModel):
    """Session creation request model"""
    title: Optional[str] = "New Chat"

class SessionResponse(BaseModel):
    """Session response model"""
    session_id: str
    title: str
    started_at: datetime
    message_count: int

class SessionUpdate(BaseModel):
    """Session update request model"""
    title: Optional[str] = None

@router.post("/session", response_model=SessionResponse, summary="Create Chat Session")
async def create_session(
    session_request: SessionCreate,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Create a new chat session
    
    Args:
        session_request: Session creation request
        current_user: Current authenticated user (optional)
        
    Returns:
        Created session information
    """
    try:
        session_id = str(uuid.uuid4())
        user_id = None
        
        # Get user ID if authenticated
        if current_user:
            user_id = await get_user_id_from_firebase_uid(current_user['uid'])
        
        # Insert new session
        execute_query(
            """
            INSERT INTO sessions (session_id, user_id, title)
            VALUES (%s, %s, %s)
            """,
            (session_id, user_id, session_request.title)
        )
        
        logger.info(f"Created session {session_id} for user {current_user['email'] if current_user else 'anonymous'}")
        
        return SessionResponse(
            session_id=session_id,
            title=session_request.title,
            started_at=datetime.utcnow(),
            message_count=0
        )
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )

@router.get("/sessions", response_model=List[SessionResponse], summary="Get User Sessions")
async def get_user_sessions(
    limit: int = 20,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all sessions for the current user
    
    Args:
        limit: Maximum number of sessions to return
        current_user: Current authenticated user
        
    Returns:
        List of user sessions
    """
    try:
        user_id = await get_user_id_from_firebase_uid(current_user['uid'])
        
        if not user_id:
            return []
        
        sessions = execute_query(
            """
            SELECT 
                s.session_id,
                s.title,
                s.started_at,
                COUNT(cm.id) as message_count
            FROM sessions s
            LEFT JOIN chat_messages cm ON s.session_id = cm.session_id
            WHERE s.user_id = %s
            GROUP BY s.session_id, s.title, s.started_at
            ORDER BY s.started_at DESC
            LIMIT %s
            """,
            (user_id, limit),
            fetch=True
        )
        
        return [
            SessionResponse(
                session_id=session["session_id"],
                title=session["title"],
                started_at=session["started_at"],
                message_count=session["message_count"]
            )
            for session in sessions
        ]
        
    except Exception as e:
        logger.error(f"Error retrieving user sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )

@router.get("/session/{session_id}", response_model=SessionResponse, summary="Get Session Details")
async def get_session(
    session_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Get details for a specific session
    
    Args:
        session_id: Session ID to retrieve
        current_user: Current authenticated user (optional)
        
    Returns:
        Session details
    """
    try:
        # Verify session access
        if current_user:
            user_id = await get_user_id_from_firebase_uid(current_user['uid'])
            if not await verify_session_access(session_id, user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this session"
                )
        
        # Get session details with message count
        session = execute_query_one(
            """
            SELECT 
                s.session_id,
                s.title,
                s.started_at,
                COUNT(cm.id) as message_count
            FROM sessions s
            LEFT JOIN chat_messages cm ON s.session_id = cm.session_id
            WHERE s.session_id = %s
            GROUP BY s.session_id, s.title, s.started_at
            """,
            (session_id,)
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return SessionResponse(
            session_id=session["session_id"],
            title=session["title"],
            started_at=session["started_at"],
            message_count=session["message_count"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session"
        )

@router.put("/session/{session_id}", response_model=SessionResponse, summary="Update Session")
async def update_session(
    session_id: str,
    update_request: SessionUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update session details
    
    Args:
        session_id: Session ID to update
        update_request: Update request data
        current_user: Current authenticated user
        
    Returns:
        Updated session details
    """
    try:
        user_id = await get_user_id_from_firebase_uid(current_user['uid'])
        
        # Verify session ownership
        if not await verify_session_access(session_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session"
            )
        
        # Update session
        if update_request.title:
            execute_query(
                """
                UPDATE sessions 
                SET title = %s, updated_at = CURRENT_TIMESTAMP
                WHERE session_id = %s
                """,
                (update_request.title, session_id)
            )
        
        # Return updated session
        return await get_session(session_id, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update session"
        )

@router.delete("/session/{session_id}", summary="Delete Session")
async def delete_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a chat session and all its messages
    
    Args:
        session_id: Session ID to delete
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    try:
        user_id = await get_user_id_from_firebase_uid(current_user['uid'])
        
        # Verify session ownership
        if not await verify_session_access(session_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session"
            )
        
        # Delete session (messages will be deleted by CASCADE)
        result = execute_query(
            "DELETE FROM sessions WHERE session_id = %s",
            (session_id,)
        )
        
        if result == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        logger.info(f"Deleted session {session_id} for user {current_user['email']}")
        return {"message": "Session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )

# Helper functions

async def get_user_id_from_firebase_uid(firebase_uid: str) -> Optional[str]:
    """
    Get database user ID from Firebase UID
    
    Args:
        firebase_uid: Firebase user UID
        
    Returns:
        Database user ID or None
    """
    user = execute_query_one(
        "SELECT id FROM users WHERE firebase_uid = %s",
        (firebase_uid,)
    )
    return user["id"] if user else None

async def verify_session_access(session_id: str, user_id: Optional[str]) -> bool:
    """
    Verify if user has access to a session
    
    Args:
        session_id: Session ID
        user_id: User ID
        
    Returns:
        True if access is allowed
    """
    session = execute_query_one(
        "SELECT user_id FROM sessions WHERE session_id = %s",
        (session_id,)
    )
    
    if not session:
        return False
    
    # Allow access if session is anonymous or belongs to user
    return session["user_id"] is None or session["user_id"] == user_id
