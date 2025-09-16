import sqlite3
from typing import Optional, List
from datetime import datetime
from .models import User, StockFavorite

class AuthService:
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the user database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    firebase_uid TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    ticker TEXT NOT NULL,
                    company_name TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, ticker)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS device_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, token)
                )
            """)
            conn.commit()

    def create_user_from_firebase(self, username: str, email: str, firebase_uid: str) -> Optional[User]:
        """Create a new user from Firebase authentication"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "INSERT INTO users (username, email, firebase_uid) VALUES (?, ?, ?)",
                    (username, email, firebase_uid)
                )
                user_id = cursor.lastrowid
                conn.commit()
                
                return User(
                    id=user_id,
                    username=username,
                    email=email,
                    firebase_uid=firebase_uid,
                    created_at=datetime.now(),
                    is_active=True
                )
        except sqlite3.IntegrityError:
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, username, email, firebase_uid, created_at, is_active FROM users WHERE email = ? AND is_active = 1",
                (email,)
            )
            row = cursor.fetchone()
            
            if row:
                return User(
                    id=row[0],
                    username=row[1],
                    email=row[2],
                    firebase_uid=row[3],
                    created_at=datetime.fromisoformat(row[4]) if row[4] else None,
                    is_active=bool(row[5])
                )
        return None
    
    def get_user_by_firebase_uid(self, firebase_uid: str) -> Optional[User]:
        """Get user by Firebase UID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, username, email, firebase_uid, created_at, is_active FROM users WHERE firebase_uid = ? AND is_active = 1",
                (firebase_uid,)
            )
            row = cursor.fetchone()
            
            if row:
                return User(
                    id=row[0],
                    username=row[1],
                    email=row[2],
                    firebase_uid=row[3],
                    created_at=datetime.fromisoformat(row[4]) if row[4] else None,
                    is_active=bool(row[5])
                )
        return None
    
    def add_favorite(self, user_id: int, ticker: str, company_name: Optional[str] = None) -> bool:
        """Add a stock to user's favorites"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO user_favorites (user_id, ticker, company_name) VALUES (?, ?, ?)",
                    (user_id, ticker.upper(), company_name)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False  # Already exists
    
    def remove_favorite(self, user_id: int, ticker: str) -> bool:
        """Remove a stock from user's favorites"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM user_favorites WHERE user_id = ? AND ticker = ?",
                (user_id, ticker.upper())
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def get_user_favorites(self, user_id: int) -> List[StockFavorite]:
        """Get all favorites for a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, user_id, ticker, company_name, added_at FROM user_favorites WHERE user_id = ? ORDER BY added_at DESC",
                (user_id,)
            )
            rows = cursor.fetchall()
            
            favorites = []
            for row in rows:
                favorites.append(StockFavorite(
                    id=row[0],
                    user_id=row[1],
                    ticker=row[2],
                    company_name=row[3],
                    added_at=datetime.fromisoformat(row[4]) if row[4] else None
                ))
            return favorites

    def save_device_token(self, user_id: int, token: str) -> bool:
        """Save or update a device token for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Use INSERT OR REPLACE to handle duplicates
                conn.execute("""
                    INSERT OR REPLACE INTO device_tokens (user_id, token, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (user_id, token))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error saving device token: {e}")
            return False

    def get_user_device_tokens(self, user_id: int) -> List[str]:
        """Get all active device tokens for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT token FROM device_tokens WHERE user_id = ? AND is_active = 1",
                    (user_id,)
                )
                rows = cursor.fetchall()
                return [row[0] for row in rows]
        except sqlite3.Error as e:
            print(f"Error getting device tokens: {e}")
            return []

    def deactivate_device_token(self, user_id: int, token: str) -> bool:
        """Deactivate a specific device token"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "UPDATE device_tokens SET is_active = 0 WHERE user_id = ? AND token = ?",
                    (user_id, token)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error deactivating device token: {e}")
            return False
