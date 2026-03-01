"""Shared FastAPI dependencies"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token
from app.db.database import get_db

# This tells FastAPI where the login endpoint is (for Swagger UI)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Dependency that extracts and validates the current user from JWT.
    Raises 401 if token is invalid or user doesn't exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    # Verify user still exists in DB
    conn = get_db()
    try:
        from app.db.repositories import get_user_by_username
        user = get_user_by_username(conn, username)
    finally:
        conn.close()
    if user is None:
        raise credentials_exception
    return user