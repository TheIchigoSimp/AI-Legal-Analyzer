"""Repository functions for database CRUD operations."""

import sqlite3
import logging
from typing import Optional
import json

logger = logging.getLogger(__name__)

# User Repository

def create_user(conn: sqlite3.Connection, username: str, hashed_password: str) -> dict:
    """Insert a new user and return the created user data."""
    cursor = conn.execute(
        "INSERT INTO users (username, hashed_password) VALUES (?, ?)",
        (username, hashed_password),
    )
    conn.commit()
    return get_user_by_username(conn, username)

def get_user_by_username(conn: sqlite3.Connection, username: str) -> Optional[dict]:
    """Fetch a user by username. Returns None if not found."""
    cursor = conn.execute(
        "SELECT id, username, hashed_password, created_at FROM users WHERE username = ?",
        (username,),
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def user_exists(conn: sqlite3.Connection, username: str) -> bool:
    """Check if a username is already taken."""
    cursor = conn.execute(
        "SELECT 1 FROM users WHERE username = ?", (username,)
    )
    return cursor.fetchone() is not None

# Document Repository

def create_document(
    conn: sqlite3.Connection,
    doc_id: str,
    filename: str,
    uploaded_by: str,
    page_count: int,
) -> dict:
    """Insert a new document record."""
    conn.execute(
        "INSERT INTO documents (id, filename, uploaded_by, page_count) VALUES (?, ?, ?, ?)",
        (doc_id, filename, uploaded_by, page_count),
    )
    conn.commit()
    return get_document(conn, doc_id)
def get_document(conn: sqlite3.Connection, doc_id: str) -> Optional[dict]:
    """Fetch a document by ID."""
    cursor = conn.execute(
        "SELECT id, filename, uploaded_by, page_count, created_at FROM documents WHERE id = ?",
        (doc_id,),
    )
    row = cursor.fetchone()
    return dict(row) if row else None
def list_user_documents(conn: sqlite3.Connection, username: str) -> list[dict]:
    """List all documents uploaded by a user."""
    cursor = conn.execute(
        "SELECT id, filename, uploaded_by, page_count, created_at FROM documents WHERE uploaded_by = ? ORDER BY created_at DESC",
        (username,),
    )
    return [dict(row) for row in cursor.fetchall()]

# Clause Repository

def insert_clauses(conn: sqlite3.Connection, document_id: str, clauses: list[dict]) -> None:
    """Bulk insert clauses for a document."""
    conn.executemany(
        "INSERT INTO clauses (id, document_id, section_title, text, page) VALUES (?, ?, ?, ?, ?)",
        [
            (c["clause_id"], document_id, c["section_title"], c["text"], c["page"])
            for c in clauses
        ],
    )
    conn.commit()
    logger.info("Inserted %d clauses for document %s", len(clauses), document_id)

def update_clause_classification(
    conn: sqlite3.Connection,
    clause_id: str,
    clause_type: str,
    importance: str,
    risk_level: str,
    risk_reason: str,
) -> None:
    """Update a clause with classification and risk results."""
    conn.execute(
        """UPDATE clauses 
           SET clause_type = ?, importance = ?, risk_level = ?, risk_reason = ?
           WHERE id = ?""",
        (clause_type, importance, risk_level, risk_reason, clause_id),
    )
    conn.commit()

def get_clauses_by_document(conn: sqlite3.Connection, document_id: str) -> list[dict]:
    """Fetch all clauses for a given document."""
    cursor = conn.execute(
        "SELECT * FROM clauses WHERE document_id = ? ORDER BY page, id",
        (document_id,),
    )
    return [dict(row) for row in cursor.fetchall()]

def is_document_analyzed(conn: sqlite3.Connection, doc_id: str) -> bool:
    """Check if a document has been analyzed (any clause has a clause_type)."""
    cursor = conn.execute(
        "SELECT 1 FROM clauses WHERE document_id = ? AND clause_type IS NOT NULL LIMIT 1",
        (doc_id,),
    )
    return cursor.fetchone() is not None

def delete_document(conn: sqlite3.Connection, doc_id: str) -> None:
    """Delete a document and all its clauses."""
    conn.execute("DELETE FROM clauses WHERE document_id = ?", (doc_id,))
    conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    logger.info("Deleted document %s and its clauses", doc_id)

# Chat Repository
def create_chat_session(conn: sqlite3.Connection, session_id: str, username: str, title: str, doc_id: str = None) -> dict:
    conn.execute(
        "INSERT INTO chat_sessions (id, username, doc_id, title) VALUES (?, ?, ?, ?)",
        (session_id, username, doc_id, title),
    )
    conn.commit()
    return {"id": session_id, "username": username, "doc_id": doc_id, "title": title}
def list_chat_sessions(conn: sqlite3.Connection, username: str, doc_id: str = None) -> list[dict]:
    if doc_id:
        cursor = conn.execute(
            "SELECT * FROM chat_sessions WHERE username = ? AND doc_id = ? ORDER BY created_at DESC",
            (username, doc_id),
        )
    else:
        cursor = conn.execute(
            "SELECT * FROM chat_sessions WHERE username = ? ORDER BY created_at DESC",
            (username,),
        )
    return [dict(row) for row in cursor.fetchall()]
def add_chat_message(conn: sqlite3.Connection, session_id: str, role: str, content: str, meta: dict = None) -> None:
    conn.execute(
        "INSERT INTO chat_messages (session_id, role, content, meta) VALUES (?, ?, ?, ?)",
        (session_id, role, content, json.dumps(meta) if meta else None),
    )
    conn.commit()
def get_chat_messages(conn: sqlite3.Connection, session_id: str) -> list[dict]:
    cursor = conn.execute(
        "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC",
        (session_id,),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    for r in rows:
        if r.get("meta"):
            r["meta"] = json.loads(r["meta"])
    return rows
def delete_chat_session(conn: sqlite3.Connection, session_id: str) -> None:
    conn.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
    conn.commit()