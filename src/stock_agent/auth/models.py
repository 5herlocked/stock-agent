from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class User:
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    password_hash: str = ""
    created_at: Optional[datetime] = None
    is_active: bool = True

@dataclass
class StockFavorite:
    id: Optional[int] = None
    user_id: int = 0
    ticker: str = ""
    company_name: Optional[str] = None
    added_at: Optional[datetime] = None

@dataclass
class StockData:
    ticker: str = ""
    company_name: str = ""
    price: float = 0.0
    change: float = 0.0
    change_percent: float = 0.0
    volume: int = 0
    market_cap: Optional[str] = None
