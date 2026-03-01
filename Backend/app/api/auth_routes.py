"""Authentication routes — register and login."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.models.auth import UserCreate, UserOut, Token
from app.core.security import hash_password, verify_password, create_access_token
from app.db.database import get_db
from app.db.repositories import create_user, get_user_by_username, user_exists

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate):
    """Register a new user."""
    conn = get_db()
    try:
        if user_exists(conn, user_data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )
        hashed_pw = hash_password(user_data.password)
        user = create_user(conn, user_data.username, hashed_pw)
        logger.info("User registered: %s", user_data.username)

        return UserOut(username=user["username"], created_at=user["created_at"])
    finally:
        conn.close()


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return JWT token."""
    conn = get_db()
    try:
        user = get_user_by_username(conn, form_data.username)

        if user is None or not verify_password(form_data.password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(data={"sub": user["username"]})
        logger.info("User logged in: %s", form_data.username)

        return Token(access_token=access_token)
    finally:
        conn.close()
