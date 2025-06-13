import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Create database directory if it doesn't exist
DB_DIR = Path(__file__).parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "profiles.db"

def init_db():
    """Initialize the SQLite database with required tables"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create profile access table for managing who can access which profiles
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS profile_access (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        profile_id INTEGER NOT NULL,
        access_level TEXT NOT NULL DEFAULT 'read',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (profile_id) REFERENCES executive_profiles (id)
    )
    ''')

    # Create profiles table with user_id
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS executive_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        company TEXT,
        title TEXT,
        linkedin_url TEXT,
        executive_profile TEXT,
        professional_background TEXT,
        leadership_summary TEXT,
        reputation_summary TEXT,
        strategy_summary TEXT,
        references_data TEXT,
        version INTEGER NOT NULL DEFAULT 1,
        is_latest BOOLEAN NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def save_profile(profile_data: dict, current_user_id: int) -> int:
    """Save a new version of an executive profile"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Convert complex data structures to JSON strings
    if 'references_data' in profile_data and isinstance(profile_data['references_data'], (dict, list)):
        profile_data['references_data'] = json.dumps(profile_data['references_data'])
    
    # Ensure user_id is set
    profile_data['user_id'] = current_user_id
    
    # Check if profile exists and get latest version
    cursor.execute(
        """
        SELECT ep.id, ep.version 
        FROM executive_profiles ep
        LEFT JOIN profile_access pa ON ep.id = pa.profile_id
        WHERE ep.name = ? AND ep.linkedin_url = ? AND ep.is_latest = 1
        AND (ep.user_id = ? OR pa.user_id = ?)
        """, 
        (profile_data.get('name'), profile_data.get('linkedin_url'), 
         current_user_id, current_user_id)
    )
    existing = cursor.fetchone()
    
    if existing:
        # Mark previous version as not latest
        cursor.execute(
            "UPDATE executive_profiles SET is_latest = 0 WHERE id = ?",
            (existing[0],)
        )
        # Create new version
        profile_data['version'] = existing[1] + 1
    else:
        # First version of this profile
        profile_data['version'] = 1
    
    # Always insert as new row with is_latest = 1
    profile_data['is_latest'] = 1
    profile_data['created_at'] = datetime.now().isoformat()
    profile_data['updated_at'] = datetime.now().isoformat()
    
    # Insert new version
    fields = ', '.join(profile_data.keys())
    placeholders = ', '.join('?' * len(profile_data))
    query = f"INSERT INTO executive_profiles ({fields}) VALUES ({placeholders})"
    cursor.execute(query, list(profile_data.values()))
    profile_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    return profile_id

def get_profile(profile_id: int, current_user_id: int) -> dict:
    """Retrieve a specific profile by ID if user has access"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT ep.* FROM executive_profiles ep
        LEFT JOIN profile_access pa ON ep.id = pa.profile_id
        WHERE ep.id = ? AND (ep.user_id = ? OR pa.user_id = ?)
    """, (profile_id, current_user_id, current_user_id))
    row = cursor.fetchone()
    
    if row:
        profile = dict(row)
        # Parse JSON strings back to Python objects
        if profile.get('references_data'):
            profile['references_data'] = json.loads(profile['references_data'])
        return profile
    
    conn.close()
    return None

def get_all_profiles(current_user_id: int, latest_only: bool = True) -> list:
    """
    Retrieve all profiles with basic information that the user has access to
    
    Args:
        current_user_id: ID of the current user
        latest_only: If True, returns only the latest version of each profile
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if latest_only:
        cursor.execute("""
            SELECT DISTINCT ep.id, ep.name, ep.company, ep.title, ep.linkedin_url, 
                   ep.version, ep.created_at, ep.updated_at, ep.user_id,
                   CASE WHEN ep.user_id = ? THEN 'owner' ELSE pa.access_level END as access_level
            FROM executive_profiles ep
            LEFT JOIN profile_access pa ON ep.id = pa.profile_id
            WHERE ep.is_latest = 1 
            AND (ep.user_id = ? OR pa.user_id = ?)
            ORDER BY ep.updated_at DESC
        """, (current_user_id, current_user_id, current_user_id))
    else:
        cursor.execute("""
            SELECT id, name, company, title, linkedin_url, version, created_at, updated_at 
            FROM executive_profiles 
            ORDER BY name, version DESC
        """)
    
    profiles = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return profiles

def save_user(user_data: dict) -> int:
    """Save a new user or update existing user"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    if user_data.get('id'):
        # Update existing user
        user_id = user_data['id']
        del user_data['id']  # Remove id from update data
        fields = [f"{k} = ?" for k in user_data.keys()]
        query = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
        values = list(user_data.values()) + [user_id]
        cursor.execute(query, values)
    else:
        # Insert new user
        fields = ', '.join(user_data.keys())
        placeholders = ', '.join('?' * len(user_data))
        query = f"INSERT INTO users ({fields}) VALUES ({placeholders})"
        cursor.execute(query, list(user_data.values()))
        user_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    return user_id

def get_user_by_email(email: str) -> dict:
    """Retrieve user by email"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    
    if row:
        return dict(row)
    return None

def grant_profile_access(user_id: int, profile_id: int, access_level: str = "read") -> bool:
    """Grant access to a profile for a user"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO profile_access (user_id, profile_id, access_level)
            VALUES (?, ?, ?)
        """, (user_id, profile_id, access_level))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error granting access: {e}")
        return False
    finally:
        conn.close()

def check_profile_access(user_id: int, profile_id: int) -> Optional[str]:
    """Check if user has access to a profile and return access level if they do"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT access_level FROM profile_access 
        WHERE user_id = ? AND profile_id = ?
    """, (user_id, profile_id))
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

def create_user_if_not_exists(username: str, email: str) -> int:
    """Create user if not exists and return user ID"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Check if user exists by email (since email is unique)
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        conn.close()
        return existing_user[0]
    
    # Create new user with required fields
    cursor.execute(
        "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
        (email, "temp_hash", username)  # Using temp values since we don't have real auth yet
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return user_id

def delete_profile(profile_id: int, current_user_id: int) -> bool:
    """Delete a profile by ID if user has access"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # First check if user has access to this profile
        cursor.execute("""
            SELECT ep.id FROM executive_profiles ep
            LEFT JOIN profile_access pa ON ep.id = pa.profile_id
            WHERE ep.id = ? AND (ep.user_id = ? OR pa.user_id = ?)
        """, (profile_id, current_user_id, current_user_id))
        
        if not cursor.fetchone():
            conn.close()
            return False
        
        # Delete from profile_access table first (foreign key constraint)
        cursor.execute("DELETE FROM profile_access WHERE profile_id = ?", (profile_id,))
        
        # Delete the profile
        cursor.execute("DELETE FROM executive_profiles WHERE id = ?", (profile_id,))
        
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting profile: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# Initialize database when module is imported
init_db()
