from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, AsyncGenerator
import json
import logging
import uuid
from datetime import datetime

# Import model integrations
from models.openrouter import OpenRouterModel

# Import authentication and database
from routes.auth import get_current_user
from db.connection import execute_query, execute_query_one

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class ChatMessage(BaseModel):
    """Chat message model"""
    role: str  # 'user', 'assistant', or 'system'
    content: str

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    model: str = "llama-3.1-8b"  # Default to Llama 3.1 8B
    session_id: Optional[str] = None
    stream: bool = True
    temperature: float = 0.7
    max_tokens: int = 1024

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    model: str
    session_id: str
    timestamp: datetime

# Initialize OpenRouter model instance
openrouter_model = OpenRouterModel()

# Available models mapping - Using only OpenRouter free models
AVAILABLE_MODELS = {
    "llama-3.1-8b": {
        "name": "Llama 3.1 8B",
        "description": "Meta's latest Llama model, great for general chat"
    },
    "gemma-7b": {
        "name": "Gemma 7B",
        "description": "Google's open model, excellent for conversations"
    },
    "mistral-7b": {
        "name": "Mistral 7B",
        "description": "Fast and efficient French AI model"
    },
    "openchat": {
        "name": "OpenChat 7B",
        "description": "Open-source conversational AI model"
    },
    "zephyr-7b": {
        "name": "Zephyr 7B Beta",
        "description": "HuggingFace's instruction-tuned model"
    }
}

@router.post("/", summary="Send Chat Message")
async def send_chat_message(
    chat_request: ChatRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Send a message to the selected LLM model
    
    Args:
        chat_request: Chat request containing message and parameters
        current_user: Current authenticated user (optional)
        
    Returns:
        Streaming response with generated text or JSON response
    """
    try:
        # Validate model
        if chat_request.model not in AVAILABLE_MODELS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model '{chat_request.model}' not available. Available models: {list(AVAILABLE_MODELS.keys())}"
            )
        
        # Get or create session
        session_id = chat_request.session_id
        if not session_id:
            session_id = await create_chat_session(current_user)
        
        # Store user message
        await store_message(
            session_id=session_id,
            role="user",
            content=chat_request.message,
            model=None
        )
        
        # Get conversation history
        messages = await get_conversation_history(session_id)
        
        if chat_request.stream:
            # Return streaming response
            return StreamingResponse(
                stream_chat_response(
                    messages,
                    session_id,
                    chat_request.model,
                    chat_request.temperature,
                    chat_request.max_tokens
                ),
                media_type="text/plain"
            )
        else:
            # Return complete response
            response_text = ""
            # Convert messages to dict format
            message_dicts = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]
            
            async for chunk in openrouter_model.generate_response(
                message_dicts,
                model=chat_request.model,
                stream=False,
                temperature=chat_request.temperature,
                max_tokens=chat_request.max_tokens
            ):
                response_text += chunk
            
            # Store assistant response
            await store_message(
                session_id=session_id,
                role="assistant",
                content=response_text,
                model=chat_request.model
            )
            
            return ChatResponse(
                response=response_text,
                model=chat_request.model,
                session_id=session_id,
                timestamp=datetime.utcnow()
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

async def stream_chat_response(
    messages: List[ChatMessage],
    session_id: str,
    model: str,
    temperature: float,
    max_tokens: int
) -> AsyncGenerator[str, None]:
    """
    Stream chat response from OpenRouter model
    
    Args:
        messages: Conversation history
        session_id: Chat session ID
        model: Model name
        temperature: Sampling temperature
        max_tokens: Maximum tokens
        
    Yields:
        String chunks of the response
    """
    response_text = ""
    
    try:
        # Convert messages to dict format
        message_dicts = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]
        
        async for chunk in openrouter_model.generate_response(
            message_dicts,
            model=model,
            stream=True,
            temperature=temperature,
            max_tokens=max_tokens
        ):
            response_text += chunk
            yield chunk
        
        # Store complete response in database
        await store_message(
            session_id=session_id,
            role="assistant",
            content=response_text,
            model=model
        )
        
    except Exception as e:
        logger.error(f"Error in streaming response: {e}")
        error_message = f"Error: {str(e)}"
        yield error_message

@router.get("/history", summary="Get Chat History")
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Get chat history for a session
    
    Args:
        session_id: Session ID to get history for
        limit: Maximum number of messages to return
        current_user: Current authenticated user (optional)
        
    Returns:
        List of chat messages
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
        
        messages = execute_query(
            """
            SELECT role, message, model, timestamp
            FROM chat_messages
            WHERE session_id = %s
            ORDER BY timestamp ASC
            LIMIT %s
            """,
            (session_id, limit),
            fetch=True
        )
        
        return [
            {
                "role": msg["role"],
                "content": msg["message"],
                "model": msg["model"],
                "timestamp": msg["timestamp"]
            }
            for msg in messages
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat history"
        )

@router.get("/models", summary="Get Available Models")
async def get_available_models():
    """
    Get list of available LLM models
    
    Returns:
        List of available models with their metadata
    """
    models = []
    for model_id, model_info in AVAILABLE_MODELS.items():
        models.append({
            "id": model_id,
            "name": model_info["name"],
            "description": model_info["description"]
        })
    
    return models

async def create_chat_session(user: Optional[Dict[str, Any]] = None) -> str:
    """
    Create a new chat session
    
    Args:
        user: User information (optional for anonymous sessions)
        
    Returns:
        Session ID
    """
    session_id = str(uuid.uuid4())
    user_id = None
    
    if user:
        user_id = await get_user_id_from_firebase_uid(user['uid'])
    
    execute_query(
        "INSERT INTO sessions (session_id, user_id) VALUES (%s, %s)",
        (session_id, user_id)
    )
    
    logger.info(f"Created new session: {session_id}")
    return session_id

async def store_message(
    session_id: str,
    role: str,
    content: str,
    model: Optional[str] = None
) -> None:
    """
    Store a chat message in the database
    
    Args:
        session_id: Session ID
        role: Message role (user, assistant, system)
        content: Message content
        model: Model used (for assistant messages)
    """
    execute_query(
        """
        INSERT INTO chat_messages (session_id, role, message, model)
        VALUES (%s, %s, %s, %s)
        """,
        (session_id, role, content, model)
    )

async def get_conversation_history(session_id: str) -> List[ChatMessage]:
    """
    Get conversation history for a session
    
    Args:
        session_id: Session ID
        
    Returns:
        List of ChatMessage objects
    """
    messages = execute_query(
        """
        SELECT role, message
        FROM chat_messages
        WHERE session_id = %s
        ORDER BY timestamp ASC
        """,
        (session_id,),
        fetch=True
    )
    
    return [
        ChatMessage(role=msg["role"], content=msg["message"])
        for msg in messages
    ]

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
