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
from app.utils.role_decorator import require_role, get_current_user

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


class UserUpdate(BaseModel):
    email: str = None
    password: str = None
    role: UserRole = None


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
    session: Session = Depends(get_session)
):
    """
    Register new user - first user becomes ADMIN, rest require ADMIN registration
    """
    # Check if username exists
    statement = select(User).where(User.username == data.username)
    existing_user = session.exec(statement).first()
    
    if existing_user:
        logger.warning(f"Registration attempt with existing user {data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if this is the first user
    user_count = len(session.exec(select(User)).all())
    
    # First user is ADMIN, others default to USER
    role = UserRole.ADMIN if user_count == 0 else UserRole.USER
    
    # Create new user
    hashed_pwd = hash_password(data.password)
    new_user = User(
        username=data.username,
        email=data.email,
        hashed_password=hashed_pwd,
        role=role
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
    
    logger.info(f"New user {new_user.username} registered with role {role}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": new_user.username,
        "role": new_user.role
    }


@router.put("/users/{user_id}", response_model=dict)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Update user details (ADMIN only)
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    # Update fields if provided
    if user_update.email:
        user.email = user_update.email
    if user_update.password:
        user.hashed_password = hash_password(user_update.password)
    if user_update.role:
        user.role = user_update.role
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    logger.info(f"Admin {current_user.username} updated user {user.username}")
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active
    }


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Delete user (ADMIN only)
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    session.delete(user)
    session.commit()
    
    logger.warning(f"Admin {current_user.username} deleted user {user.username}")



@router.get("/users")
def get_users(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Get all users (ADMIN only) - READ endpoint for 0.15 pkt
    """
    users = session.exec(select(User)).all()
    logger.info(f"Admin {current_user.username} retrieved {len(users)} users")
    
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at
        }
        for user in users
    ]


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
