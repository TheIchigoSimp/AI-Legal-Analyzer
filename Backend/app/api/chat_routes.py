"""Chat session endpoints."""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.repositories import (
    create_chat_session, list_chat_sessions,
    add_chat_message, get_chat_messages, delete_chat_session
)
from app.services.qa_chain import ask_question
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    question: str
    doc_id: Optional[str] = None
    top_k: int = 5

@router.get("/sessions")
def get_sessions(doc_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    try:
        return list_chat_sessions(conn, current_user["username"], doc_id)
    finally:
        conn.close()

@router.get("/sessions/{session_id}/messages")
def get_messages(session_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    try:
        return get_chat_messages(conn, session_id)
    finally:
        conn.close()

@router.post("/send")
def send_message(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    try:
        # Create session if not provided
        if not req.session_id:
            session_id = str(uuid.uuid4())
            title = req.question[:50] + ("..." if len(req.question) > 50 else "")
            create_chat_session(conn, session_id, current_user["username"], title, req.doc_id)
        else:
            session_id = req.session_id

        # Save user message
        add_chat_message(conn, session_id, "user", req.question)

        # Get conversation history for memory
        history = get_chat_messages(conn, session_id)
        # Exclude the message we just added (last one) to avoid duplication
        conversation_history = [
            {"role": m["role"], "content": m["content"]}
            for m in history[:-1]
        ]

        # Get AI answer with memory
        result = ask_question(
            req.question,
            top_k=req.top_k,
            doc_id=req.doc_id,
            conversation_history=conversation_history if conversation_history else None,
        )

        # Save assistant message
        meta = {
            "referenced_clauses": result.referenced_clauses,
            "overall_risk": result.overall_risk,
            "confidence": result.confidence,
        }
        add_chat_message(conn, session_id, "assistant", result.answer, meta)

        return {
            "session_id": session_id,
            "answer": result.answer,
            "referenced_clauses": result.referenced_clauses,
            "overall_risk": result.overall_risk,
            "confidence": result.confidence,
        }
    finally:
        conn.close()

@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    try:
        delete_chat_session(conn, session_id)
        return {"ok": True}
    finally:
        conn.close()
