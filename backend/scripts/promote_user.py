#!/usr/bin/env python3
"""
Utility script to promote a user to ADMIN role or create an ADMIN user.
Usage: python promote_user.py <username> [--create]
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlmodel import Session, select, SQLModel
from app.db.session import engine
from app.db.models import User, UserRole
from app.utils.jwt_utils import hash_password


def init_db():
    """Create all tables if they don't exist."""
    SQLModel.metadata.create_all(engine)

def promote_user(username: str):
    """Promote existing user to ADMIN role."""
    with Session(engine) as session:
        statement = select(User).where(User.username == username)
        user = session.exec(statement).first()
        
        if not user:
            print(f"❌ User '{username}' not found")
            return False
        
        user.role = UserRole.ADMIN
        session.add(user)
        session.commit()
        print(f"✓ User '{username}' promoted to ADMIN")
        return True


def create_admin(username: str, password: str, email: str = None):
    """Create new ADMIN user."""
    with Session(engine) as session:
        # Check if user exists
        statement = select(User).where(User.username == username)
        existing = session.exec(statement).first()
        
        if existing:
            print(f"❌ User '{username}' already exists")
            return False
        
        # Create admin user
        admin = User(
            username=username,
            email=email or f"{username}@admin.local",
            hashed_password=hash_password(password),
            role=UserRole.ADMIN,
            is_active=True
        )
        session.add(admin)
        session.commit()
        print(f"✓ ADMIN user '{username}' created successfully")
        print(f"  Email: {admin.email}")
        print(f"  Role: {admin.role}")
        return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python promote_user.py <username>              # Promote existing user to ADMIN")
        print("  python promote_user.py <username> <password>   # Create new ADMIN user")
        sys.exit(1)
    
    # Initialize database tables
    print("Initializing database...")
    init_db()
    print("✓ Database ready\n")
    
    username = sys.argv[1]
    
    if len(sys.argv) >= 3:
        # Create new admin
        password = sys.argv[2]
        email = sys.argv[3] if len(sys.argv) >= 4 else None
        create_admin(username, password, email)
    else:
        # Promote existing user
        promote_user(username)
