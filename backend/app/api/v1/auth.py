from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel
from datetime import timedelta
import logging

from app.db.session import get_session
from app.db.models import User, UserRole
from app.utils.jwt_utils import (
    hash_password,
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.utils.role_decorator import require_role

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str = None


@router.post("/login", response_model=LoginResponse)
def login(
    credentials: LoginRequest,
    session: Session = Depends(get_session)
):
    """
    Login user and return JWT access token with role
    """
    # Find user by username
    statement = select(User).where(User.username == credentials.username)
    user = session.exec(statement).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        logger.warning(f"Failed login attempt for username: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        logger.warning(f"Inactive user {credentials.username} attempted login")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )
    
    # Create JWT token with role
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role},
        expires_delta=access_token_expires
    )
    
    logger.info(f"User {user.username} ({user.role}) logged in")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role
    }


@router.post("/register", response_model=LoginResponse)
def register(
    data: RegisterRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Register new user (ADMIN only)
    """
    # Check if username exists
    statement = select(User).where(User.username == data.username)
    existing_user = session.exec(statement).first()
    
    if existing_user:
        logger.warning(f"Admin {current_user.username} attempted to register existing user {data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create new user with USER role by default
    hashed_pwd = hash_password(data.password)
    new_user = User(
        username=data.username,
        email=data.email,
        hashed_password=hashed_pwd,
        role=UserRole.USER
    )
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    # Return token immediately after registration
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.username, "user_id": new_user.id, "role": new_user.role},
        expires_delta=access_token_expires
    )
    
    logger.info(f"Admin {current_user.username} registered new user {new_user.username}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": new_user.username,
        "role": new_user.role
    }


@router.post("/logout")
def logout():
    """
    Logout endpoint (token invalidation handled on frontend by removing token)
    """
    logger.debug("User logout requested")
    return {
        "message": "Successfully logged out",
        "status": "success"
    }
