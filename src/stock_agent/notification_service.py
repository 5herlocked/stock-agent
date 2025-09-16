from typing import Dict, Any, Optional
import firebase_admin
from firebase_admin import messaging, credentials
import os
from dataclasses import dataclass
from datetime import datetime

@dataclass
class StockAlert:
    ticker: str
    percent_change: float
    current_price: float
    alert_type: str  # 'gainer' or 'loser'
    timestamp: datetime = datetime.now()

class NotificationService:
    def __init__(self, creds_path: Optional[str] = None):
        """Initialize Firebase with credentials if not already initialized"""
        # Check if Firebase is already initialized
        if not firebase_admin._apps:
            if not creds_path:
                creds_path = os.getenv('FIREBASE_CREDS_PATH')

            if not creds_path:
                raise ValueError("Firebase credentials path not provided")

            cred = credentials.Certificate(creds_path)
            firebase_admin.initialize_app(cred)
        else:
            print("Firebase already initialized, reusing existing app")

    def send_notification_to_topic(self, topic: str, alert: StockAlert) -> bool:
        """Send a notification to all devices subscribed to a specific topic"""
        try:
            message = messaging.Message(
                data={
                    'ticker': alert.ticker,
                    'percent_change': f"{alert.percent_change:.2f}",
                    'current_price': f"{alert.current_price:.2f}",
                    'alert_type': alert.alert_type,
                    'timestamp': alert.timestamp.isoformat(),
                },
                notification=messaging.Notification(
                    title=f"Stock {alert.alert_type.title()} Alert: {alert.ticker}",
                    body=f"{alert.ticker} has moved {alert.percent_change:.2f}% " \
                         f"({'up' if alert.percent_change > 0 else 'down'}) " \
                         f"to ${alert.current_price:.2f}"
                ),
                topic=topic,
            )

            response = messaging.send(message)
            print(f"Response: {response}")
            return bool(response)
        except Exception as e:
            print(f"Error sending notification: {str(e)}")
            return False

    def subscribe_to_topic(self, token: str, topic: str) -> bool:
        """Subscribe a device token to a specific topic"""
        try:
            response = messaging.subscribe_to_topic(tokens=[token], topic=topic)
            return response.success_count > 0
        except Exception as e:
            print(f"Error subscribing to topic: {str(e)}")
            return False

    def unsubscribe_from_topic(self, token: str, topic: str) -> bool:
        """Unsubscribe a device token from a specific topic"""
        try:
            response = messaging.unsubscribe_from_topic(tokens=[token], topic=topic)
            return response.success_count > 0
        except Exception as e:
            print(f"Error unsubscribing from topic: {str(e)}")
            return False
