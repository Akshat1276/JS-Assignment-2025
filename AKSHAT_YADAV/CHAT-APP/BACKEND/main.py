# backend/main.py
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from db import get_db_connection
from pydantic import BaseModel
from models.openrouter import call_openrouter
import uuid
import os
import psycopg2
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
def read_root():
    return {"msg": "LLM Chat Backend is running"}


# Pydantic models
class SessionRequest(BaseModel):
    user_id: str = None  # Optional, but not required anymore

class SessionResponse(BaseModel):
    session_id: str

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    session_id: str
    model: str
    message: str

class ChatResponse(BaseModel):
    response: str

class ChatHistoryResponse(BaseModel):
    history: List[ChatMessage]

@app.get("/db-test")
def db_test():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return {"db_connection": "success", "result": result}
    except Exception as e:
        return {"db_connection": "failed", "error": str(e)}


# /chat/session endpoint
@app.post("/chat/session", response_model=SessionResponse)
def chat_session(payload: SessionRequest):
    conn = get_db_connection()
    cur = conn.cursor()
    # Create new session (no user required)
    session_id = str(uuid.uuid4())
    cur.execute("INSERT INTO sessions (session_id) VALUES (%s)", (session_id,))
    conn.commit()
    cur.close()
    conn.close()
    return SessionResponse(session_id=session_id)

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    conn = get_db_connection()
    cur = conn.cursor()
    # Get previous messages for context
    cur.execute("SELECT role, message FROM chat_messages WHERE session_id = %s ORDER BY timestamp ASC", (request.session_id,))
    history = [{"role": row[0], "content": row[1]} for row in cur.fetchall()]
    # Add the new user message
    history.append({"role": "user", "content": request.message})
    # Call the LLM
    response = call_openrouter(request.model, history)
    # Save user message
    cur.execute(
        "INSERT INTO chat_messages (id, session_id, role, message, model) VALUES (%s, %s, %s, %s, %s)",
        (str(uuid.uuid4()), request.session_id, "user", request.message, request.model)
    )
    # Save assistant message
    cur.execute(
        "INSERT INTO chat_messages (id, session_id, role, message, model) VALUES (%s, %s, %s, %s, %s)",
        (str(uuid.uuid4()), request.session_id, "assistant", response, request.model)
    )
    conn.commit()
    cur.close()
    conn.close()
    return ChatResponse(response=response)

@app.get("/chat/history", response_model=ChatHistoryResponse)
def chat_history(session_id: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT role, message FROM chat_messages WHERE session_id = %s ORDER BY timestamp ASC", (session_id,))
    history = [ChatMessage(role=row[0], content=row[1]) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return ChatHistoryResponse(history=history)

# --- New endpoint to list all sessions (for sidebar)
@app.get("/chat/sessions")
def list_sessions():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT session_id FROM sessions ORDER BY session_id DESC")
    sessions = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return {"sessions": sessions}