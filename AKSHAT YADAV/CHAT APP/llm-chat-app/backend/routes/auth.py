from fastapi import APIRouter, HTTPException, Depends, Header, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from auth.firebase import verify_firebase_token, mock_verify_token
from db.connection import execute_query, execute_query_one
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class TokenRequest(BaseModel):
    """Request model for token verification"""
    id_token: str

class UserResponse(BaseModel):
    """Response model for user data"""
    uid: str
    email: str
    name: str
    email_verified: bool

async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user
    
    Args:
        authorization: Authorization header with Bearer token
        
    Returns:
        Dictionary containing user information
        
    Raises:
        HTTPException: If authentication fails
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # For development, allow mock authentication
        if os.getenv("ENVIRONMENT") == "development" and token == "mock_token":
            return mock_verify_token(token)
        
        # Verify Firebase token
        user_info = verify_firebase_token(token)
        return user_info
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )

@router.post("/verify", response_model=UserResponse, summary="Verify Firebase ID Token")
async def verify_token(token_request: TokenRequest):
    """
    Verify Firebase ID token and return user information
    
    Args:
        token_request: Request containing the ID token
        
    Returns:
        User information if token is valid
        
    Raises:
        HTTPException: If token verification fails
    """
    try:
        # For development, allow mock authentication
        if (os.getenv("ENVIRONMENT") == "development" and 
            token_request.id_token == "mock_token"):
            user_info = mock_verify_token(token_request.id_token)
        else:
            # Verify Firebase token
            user_info = verify_firebase_token(token_request.id_token)
        
        # Store or update user in database
        await store_user_in_db(user_info)
        
        return UserResponse(
            uid=user_info['uid'],
            email=user_info['email'],
            name=user_info['name'],
            email_verified=user_info.get('email_verified', False)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed"
        )

@router.get("/user", response_model=UserResponse, summary="Get Current User")
async def get_user(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get current authenticated user information
    
    Args:
        current_user: Current user from authentication dependency
        
    Returns:
        Current user information
    """
    return UserResponse(
        uid=current_user['uid'],
        email=current_user['email'],
        name=current_user['name'],
        email_verified=current_user.get('email_verified', False)
    )

@router.post("/logout", summary="Logout User")
async def logout_user(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Logout user (placeholder for client-side token removal)
    
    Args:
        current_user: Current user from authentication dependency
        
    Returns:
        Success message
    """
    logger.info(f"User {current_user['email']} logged out")
    return {"message": "Logged out successfully"}

async def store_user_in_db(user_info: Dict[str, Any]) -> None:
    """
    Store or update user information in the database
    
    Args:
        user_info: User information from Firebase
    """
    try:
        # Check if user already exists
        existing_user = execute_query_one(
            "SELECT id FROM users WHERE firebase_uid = %s",
            (user_info['uid'],)
        )
        
        if existing_user:
            # Update existing user
            execute_query(
                """
                UPDATE users 
                SET email = %s, name = %s, updated_at = CURRENT_TIMESTAMP
                WHERE firebase_uid = %s
                """,
                (user_info['email'], user_info['name'], user_info['uid'])
            )
            logger.info(f"Updated user: {user_info['email']}")
        else:
            # Insert new user
            execute_query(
                """
                INSERT INTO users (firebase_uid, email, name)
                VALUES (%s, %s, %s)
                """,
                (user_info['uid'], user_info['email'], user_info['name'])
            )
            logger.info(f"Created new user: {user_info['email']}")
            
    except Exception as e:
        logger.error(f"Failed to store user in database: {e}")
        # Don't raise exception here to avoid blocking authentication
