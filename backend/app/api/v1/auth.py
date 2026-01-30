from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel
from datetime import timedelta

from app.db.session import get_session
from app.db.models import User
from app.utils.jwt_utils import (
    hash_password,
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    username: str


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
    Login user and return JWT access token
    """
    # Find user by username
    statement = select(User).where(User.username == credentials.username)
    user = session.exec(statement).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )
    
    # Create JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username
    }


@router.post("/register", response_model=LoginResponse)
def register(
    data: RegisterRequest,
    session: Session = Depends(get_session)
):
    """
    Register new user
    """
    # Check if username exists
    statement = select(User).where(User.username == data.username)
    existing_user = session.exec(statement).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create new user
    hashed_pwd = hash_password(data.password)
    new_user = User(
        username=data.username,
        email=data.email,
        hashed_password=hashed_pwd
    )
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    # Return token immediately after registration
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.username, "user_id": new_user.id},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": new_user.username
    }


@router.post("/logout")
def logout():
    """
    Logout endpoint (token invalidation handled on frontend by removing token)
    Backend just acknowledges logout
    """
    return {
        "message": "Successfully logged out",
        "status": "success"
    }
