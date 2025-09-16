#!/usr/bin/env python3
"""
Stock Agent Admin CLI Tool

This tool allows administrators to view users and test notifications.
Users are automatically created via Firebase authentication.
"""

import argparse
import sys

from ..auth import AuthService
from ..notification_service import NotificationService, StockAlert


def list_users(auth_service: AuthService):
    """List all users in the system (Firebase-authenticated users)"""
    import sqlite3

    try:
        with sqlite3.connect(auth_service.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, username, email, firebase_uid, created_at, is_active
                FROM users
                ORDER BY created_at DESC
            """)
            users = cursor.fetchall()

            if not users:
                print("No users found in the system.")
                print("Users are automatically created when they authenticate via Firebase.")
                return

            print("\n📋 User List (Firebase-authenticated users):")
            print("-" * 100)
            print(f"{'ID':<4} {'Username':<20} {'Email':<30} {'Firebase UID':<20} {'Created':<20} {'Active':<6}")
            print("-" * 100)

            for user in users:
                user_id, username, email, firebase_uid, created_at, is_active = user
                status = "✅" if is_active else "❌"
                created_str = created_at[:19] if created_at else "Unknown"
                firebase_uid_short = firebase_uid[:18] + "..." if firebase_uid and len(firebase_uid) > 20 else firebase_uid or "None"
                print(f"{user_id:<4} {username:<20} {email:<30} {firebase_uid_short:<20} {created_str:<20} {status:<6}")

            print("-" * 100)
            print(f"Total users: {len(users)}")
            print("Note: Users are automatically created via Firebase authentication")

    except Exception as e:
        print(f"❌ Error listing users: {e}")





def test_notification(topic: str = "stock_alerts", ticker: str = "AAPL") -> bool:
    """Send a test push notification to all users"""
    try:
        # Initialize notification service
        notification_service = NotificationService()

        # Create a test stock alert
        test_alert = StockAlert(
            ticker=ticker,
            percent_change=5.25,
            current_price=175.50,
            alert_type="gainer"
        )

        print(f"📱 Sending test notification for {ticker} to topic '{topic}'...")
        success = notification_service.send_notification_to_topic(topic, test_alert)

        if success:
            print(f"✅ Test notification sent successfully!")
            print(f"   Ticker: {ticker}")
            print(f"   Message: {ticker} has moved 5.25% up to $175.50")
            return True
        else:
            print(f"❌ Failed to send test notification")
            return False

    except Exception as e:
        print(f"❌ Error sending test notification: {e}")
        return False


def main():
    """Main CLI entry point"""

    from dotenv import load_dotenv

    load_dotenv(".dev.env")

    parser = argparse.ArgumentParser(
        description="Stock Agent Admin Tool - Manage users and system administration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s create-user john john@example.com
  %(prog)s list-users
  %(prog)s deactivate-user john
  %(prog)s activate-user john
  %(prog)s reset-password john
  %(prog)s test-notification
  %(prog)s test-notification --topic custom_topic --ticker TSLA
        """
    )

    parser.add_argument(
        '--db-path',
        default='users.db',
        help='Path to the user database (default: users.db)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Create user command
    create_parser = subparsers.add_parser('create-user', help='Create a new user')
    create_parser.add_argument('username', help='Username for the new user')
    create_parser.add_argument('email', help='Email address for the new user')
    create_parser.add_argument('--password', help='Password (will prompt if not provided)')

    # List users command
    subparsers.add_parser('list-users', help='List all users in the system')

    # Deactivate user command
    deactivate_parser = subparsers.add_parser('deactivate-user', help='Deactivate a user account')
    deactivate_parser.add_argument('username', help='Username to deactivate')

    # Activate user command
    activate_parser = subparsers.add_parser('activate-user', help='Activate a user account')
    activate_parser.add_argument('username', help='Username to activate')

    # Reset password command
    reset_parser = subparsers.add_parser('reset-password', help='Reset a user\'s password')
    reset_parser.add_argument('username', help='Username to reset password for')

    # Test notification command
    test_notif_parser = subparsers.add_parser('test-notification', help='Send a test push notification')
    test_notif_parser.add_argument('--topic', default='stock_alerts', help='Firebase topic to send to (default: stock_alerts)')
    test_notif_parser.add_argument('--ticker', default='AAPL', help='Stock ticker for test notification (default: AAPL)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize auth service
    auth_service = AuthService(db_path=args.db_path)

    print(f"🔧 Stock Agent Admin Tool (Firebase Auth)")
    print(f"📁 Database: {args.db_path}")
    print()

    # Execute commands
    if args.command == 'list-users':
        list_users(auth_service)

    elif args.command == 'test-notification':
        success = test_notification(args.topic, args.ticker)
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
