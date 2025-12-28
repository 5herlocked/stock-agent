import sqlite3
from typing import Optional, List, Dict
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

            conn.execute("""
                CREATE TABLE IF NOT EXISTS whatsapp_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    company_name TEXT,
                    price REAL,
                    change_percent REAL,
                    from_sender TEXT NOT NULL,
                    chat_name TEXT NOT NULL,
                    original_message TEXT NOT NULL,
                    received_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    ticker TEXT NOT NULL,
                    action TEXT NOT NULL CHECK(action IN ('BUY', 'SELL')),
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    trade_date TEXT NOT NULL,
                    notes TEXT,
                    whatsapp_recommendation_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (whatsapp_recommendation_id) REFERENCES whatsapp_recommendations (id)
                )
            """)

            # Add status column to whatsapp_recommendations if it doesn't exist
            try:
                conn.execute("""
                    ALTER TABLE whatsapp_recommendations
                    ADD COLUMN status TEXT DEFAULT 'pending'
                    CHECK(status IN ('pending', 'accepted', 'rejected'))
                """)
            except sqlite3.OperationalError:
                # Column already exists, ignore
                pass

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

    def save_whatsapp_recommendation(self, ticker: str, company_name: Optional[str], price: Optional[float],
                                     change_percent: Optional[float], from_sender: str, chat_name: str,
                                     original_message: str, received_at: str) -> bool:
        """Save a WhatsApp recommendation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO whatsapp_recommendations
                    (ticker, company_name, price, change_percent, from_sender, chat_name, original_message, received_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (ticker.upper(), company_name, price, change_percent, from_sender, chat_name, original_message, received_at))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error saving WhatsApp recommendation: {e}")
            return False

    def get_whatsapp_recommendations(self, limit: int = 50, status: Optional[str] = None):
        """Get recent WhatsApp recommendations"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if status:
                    cursor = conn.execute("""
                        SELECT id, ticker, company_name, price, change_percent, from_sender,
                               chat_name, original_message, received_at, created_at, status
                        FROM whatsapp_recommendations
                        WHERE status = ?
                        ORDER BY received_at DESC
                        LIMIT ?
                    """, (status, limit))
                else:
                    cursor = conn.execute("""
                        SELECT id, ticker, company_name, price, change_percent, from_sender,
                               chat_name, original_message, received_at, created_at, status
                        FROM whatsapp_recommendations
                        ORDER BY received_at DESC
                        LIMIT ?
                    """, (limit,))
                rows = cursor.fetchall()

                recommendations = []
                for row in rows:
                    recommendations.append({
                        'id': row[0],
                        'ticker': row[1],
                        'company_name': row[2],
                        'price': row[3],
                        'change_percent': row[4],
                        'from_sender': row[5],
                        'chat_name': row[6],
                        'original_message': row[7],
                        'received_at': row[8],
                        'created_at': row[9],
                        'status': row[10] if len(row) > 10 else 'pending'
                    })
                return recommendations
        except sqlite3.Error as e:
            print(f"Error getting WhatsApp recommendations: {e}")
            return []

    def add_trade(self, user_id: int, ticker: str, action: str, quantity: int,
                  price: float, trade_date: str, notes: Optional[str] = None,
                  whatsapp_recommendation_id: Optional[int] = None) -> Optional[int]:
        """Add a new trade. Returns trade_id if successful."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    INSERT INTO trades (user_id, ticker, action, quantity, price, trade_date, notes, whatsapp_recommendation_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, ticker.upper(), action.upper(), quantity, price, trade_date, notes, whatsapp_recommendation_id))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error adding trade: {e}")
            return None

    def get_user_trades(self, user_id: int, limit: int = 100) -> List[Dict]:
        """Get all trades for a user, ordered by trade_date DESC."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT id, user_id, ticker, action, quantity, price, trade_date, notes, whatsapp_recommendation_id, created_at
                    FROM trades
                    WHERE user_id = ?
                    ORDER BY trade_date DESC, created_at DESC
                    LIMIT ?
                """, (user_id, limit))
                rows = cursor.fetchall()

                trades = []
                for row in rows:
                    trades.append({
                        'id': row[0],
                        'user_id': row[1],
                        'ticker': row[2],
                        'action': row[3],
                        'quantity': row[4],
                        'price': row[5],
                        'trade_date': row[6],
                        'notes': row[7],
                        'whatsapp_recommendation_id': row[8],
                        'created_at': row[9]
                    })
                return trades
        except sqlite3.Error as e:
            print(f"Error getting trades: {e}")
            return []

    def delete_trade(self, user_id: int, trade_id: int) -> bool:
        """Delete a trade. Returns True if successful."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM trades WHERE id = ? AND user_id = ?",
                    (trade_id, user_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error deleting trade: {e}")
            return False

    def get_user_positions(self, user_id: int) -> List[Dict]:
        """Calculate current positions grouped by ticker from trades."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT ticker, action, quantity, price
                    FROM trades
                    WHERE user_id = ?
                    ORDER BY ticker, trade_date
                """, (user_id,))

                trades = cursor.fetchall()

                positions = {}
                for ticker, action, quantity, price in trades:
                    if ticker not in positions:
                        positions[ticker] = {
                            'ticker': ticker,
                            'total_bought': 0,
                            'total_sold': 0,
                            'total_cost': 0.0
                        }

                    if action == 'BUY':
                        positions[ticker]['total_bought'] += quantity
                        positions[ticker]['total_cost'] += (quantity * price)
                    elif action == 'SELL':
                        positions[ticker]['total_sold'] += quantity

                result = []
                for ticker, data in positions.items():
                    total_quantity = data['total_bought'] - data['total_sold']

                    if total_quantity == 0:
                        continue

                    avg_cost = data['total_cost'] / data['total_bought'] if data['total_bought'] > 0 else 0

                    result.append({
                        'ticker': ticker,
                        'total_quantity': total_quantity,
                        'avg_cost': avg_cost,
                        'total_cost_basis': avg_cost * total_quantity
                    })

                return result
        except sqlite3.Error as e:
            print(f"Error getting positions: {e}")
            return []

    def update_whatsapp_recommendation_status(self, recommendation_id: int, status: str) -> bool:
        """Update status of a recommendation (pending/accepted/rejected)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "UPDATE whatsapp_recommendations SET status = ? WHERE id = ?",
                    (status, recommendation_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error updating recommendation status: {e}")
            return False
