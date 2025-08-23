import sqlite3
import bcrypt
import secrets
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from .models import User, StockFavorite

class AuthService:
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self._init_db()

    def _init_db(self):
        """Initialize the user database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
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
            conn.commit()

    def _hash_password(self, password: str) -> str:
        """Hash password with salt using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def register_user(self, username: str, email: str, password: str) -> Optional[User]:
        """Register a new user"""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        password_hash = self._hash_password(password)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username, email, password_hash)
                )
                user_id = cursor.lastrowid
                conn.commit()
                
                return User(
                    id=user_id,
                    username=username,
                    email=email,
                    password_hash=password_hash,
                    created_at=datetime.now(),
                    is_active=True
                )
        except sqlite3.IntegrityError:
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, username, email, password_hash, created_at, is_active FROM users WHERE username = ? AND is_active = 1",
                (username,)
            )
            row = cursor.fetchone()
            
            if row and self._verify_password(password, row[3]):
                return User(
                    id=row[0],
                    username=row[1],
                    email=row[2],
                    password_hash=row[3],
                    created_at=datetime.fromisoformat(row[4]) if row[4] else None,
                    is_active=bool(row[5])
                )
        return None

    def create_session(self, user: User) -> str:
        """Create a session token for authenticated user"""
        session_token = secrets.token_urlsafe(32)
        self.sessions[session_token] = {
            'user_id': user.id,
            'username': user.username,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(hours=24)
        }
        return session_token
    
    def get_user_from_session(self, session_token: str) -> Optional[User]:
        """Get user from session token"""
        if session_token not in self.sessions:
            return None
        
        session = self.sessions[session_token]
        if datetime.now() > session['expires_at']:
            del self.sessions[session_token]
            return None
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, username, email, password_hash, created_at, is_active FROM users WHERE id = ? AND is_active = 1",
                (session['user_id'],)
            )
            row = cursor.fetchone()
            
            if row:
                return User(
                    id=row[0],
                    username=row[1],
                    email=row[2],
                    password_hash=row[3],
                    created_at=datetime.fromisoformat(row[4]) if row[4] else None,
                    is_active=bool(row[5])
                )
        return None
    
    def logout(self, session_token: str) -> bool:
        """Logout user by removing session"""
        if session_token in self.sessions:
            del self.sessions[session_token]
            return True
        return False
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired_tokens = [
            token for token, session in self.sessions.items()
            if now > session['expires_at']
        ]
        for token in expired_tokens:
            del self.sessions[token]
    
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
