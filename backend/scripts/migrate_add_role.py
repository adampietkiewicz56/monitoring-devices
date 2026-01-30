"""
Migration script to add role column to user table
"""
import sqlite3
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

DB_PATH = "monitoring.db"


def migrate():
    """Add role column to user table if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if role column exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'role' in columns:
            print("✓ Column 'role' already exists in user table")
            return
        
        # Add role column with default value 'USER'
        print("Adding 'role' column to user table...")
        cursor.execute("""
            ALTER TABLE user 
            ADD COLUMN role VARCHAR NOT NULL DEFAULT 'USER'
        """)
        
        conn.commit()
        print("✓ Migration completed successfully")
        print("  - Added 'role' column with default value 'USER'")
        
        # Show current users
        cursor.execute("SELECT id, username, role FROM user")
        users = cursor.fetchall()
        if users:
            print("\nCurrent users:")
            for user_id, username, role in users:
                print(f"  - {username} (ID: {user_id}, Role: {role})")
        
    except sqlite3.Error as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 50)
    print("DATABASE MIGRATION: Add role column")
    print("=" * 50)
    migrate()
