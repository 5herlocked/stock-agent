import asyncio
from datetime import datetime, time
from typing import Optional, List, Dict
import os
from .index_tracker import IndexTracker
from .market_analyzer import MarketAnalyzer
from .notification_service import NotificationService, StockAlert

class StockMonitoringService:
    def __init__(self):
        self.tracker = IndexTracker()
        self.analyzer = MarketAnalyzer()
        self.notification_service = NotificationService()

        # Get device token from environment
        self.device_token = os.getenv('DEVICE_TOKEN')
        if not self.device_token:
            raise ValueError("DEVICE_TOKEN environment variable not set")

        # Configure thresholds
        self.movement_threshold = float(os.getenv('MOVEMENT_THRESHOLD', '5.0'))  # 5% default

        # Track last notification times to prevent spam
        self.last_notifications: Dict[str, datetime] = {}

    async def run_market_check(self):
        """Run a single market check and send notifications if needed"""
        try:
            # Get all constituents
            constituents = self.tracker.get_all_index_constituents()

            # Analyze movements
            movements = self.analyzer.calculate_price_changes(list(constituents))

            # Filter significant movements
            significant_moves = [
                m for m in movements
                if abs(m["percent_change"]) >= self.movement_threshold
            ]

            # Send notifications for significant movements
            for move in significant_moves:
                # Don't notify about the same stock more than once per day
                last_notif = self.last_notifications.get(move["ticker"])
                if last_notif and (datetime.now() - last_notif).days < 1:
                    continue

                alert = StockAlert(
                    ticker=move["ticker"],
                    percent_change=move["percent_change"],
                    current_price=move["end_price"],
                    alert_type="gainer" if move["percent_change"] > 0 else "loser"
                )

                if self.notification_service.send_notification(self.device_token, alert):
                    self.last_notifications[move["ticker"]] = datetime.now()

        except Exception as e:
            print(f"Error in market check: {str(e)}")
