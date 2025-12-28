#!/usr/bin/env python3
"""
Stock Agent Admin CLI Tool

This tool allows administrators to view users and test notifications.
Users are automatically created via Firebase authentication.
"""

import argparse
import sys
import os
import getpass

from ..auth import AuthService
from ..notification_service import NotificationService, StockAlert
from firebase_admin import auth as firebase_auth
import firebase_admin
from firebase_admin import credentials
import json


def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    if firebase_admin._apps:
        return

    try:
        creds_path = os.getenv('FIREBASE_CREDS_PATH')
        if creds_path and os.path.exists(creds_path):
            cred = credentials.Certificate(creds_path)
        else:
            service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
            if service_account_json:
                service_account_info = json.loads(service_account_json)
                cred = credentials.Certificate(service_account_info)
            else:
                cred = credentials.ApplicationDefault()

        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"❌ Failed to initialize Firebase Admin SDK: {e}")
        sys.exit(1)


def create_user(email: str, password: str, username: str, auth_service: AuthService) -> bool:
    """Create a new user in Firebase and local database"""
    try:
        initialize_firebase()

        print(f"Creating Firebase user for {email}...")

        # Create user in Firebase
        firebase_user = firebase_auth.create_user(
            email=email,
            password=password,
            email_verified=True,
            display_name=username
        )

        print(f"✅ Firebase user created with UID: {firebase_user.uid}")

        # Create user in local database
        local_user = auth_service.create_user_from_firebase(
            username=username,
            email=email,
            firebase_uid=firebase_user.uid
        )

        if local_user:
            print(f"✅ Local database user created with ID: {local_user.id}")
            print(f"\n🎉 User created successfully!")
            print(f"   Email: {email}")
            print(f"   Username: {username}")
            print(f"   Firebase UID: {firebase_user.uid}")
            return True
        else:
            print(f"❌ Failed to create user in local database (user may already exist)")
            # Clean up Firebase user
            print(f"Cleaning up Firebase user...")
            firebase_auth.delete_user(firebase_user.uid)
            return False

    except firebase_auth.EmailAlreadyExistsError:
        print(f"❌ User with email {email} already exists in Firebase")
        return False
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return False


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
                print("Use 'create-user' command to add new users.")
                return

            print("\n📋 User List:")
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

    except Exception as e:
        print(f"❌ Error listing users: {e}")





def test_notification(topic: str = "stock_update", ticker: str = "AAPL") -> bool:
    """Send a test push notification to all users"""
    try:
        # Initialize notification service
        notification_service = NotificationService()

        # Create a test stock alert
        test_alert = StockAlert(
            ticker=ticker,
            percent_change=5.25,
            current_price=175.50,
            alert_type="stock_update"
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
  %(prog)s create-user --email user@example.com --username johndoe
  %(prog)s list-users
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
    create_user_parser = subparsers.add_parser('create-user', help='Create a new user in Firebase and local database')
    create_user_parser.add_argument('--email', required=True, help='User email address')
    create_user_parser.add_argument('--username', required=True, help='Username for the user')
    create_user_parser.add_argument('--password', help='Password for the user (will prompt if not provided)')

    # List users command
    subparsers.add_parser('list-users', help='List all users in the system')

    # Test notification command
    test_notif_parser = subparsers.add_parser('test-notification', help='Send a test push notification')
    test_notif_parser.add_argument('--topic', default='stock_updates', help='Firebase topic to send to (default: stock_updates)')
    test_notif_parser.add_argument('--ticker', default='AAPL', help='Stock ticker for test notification (default: AAPL)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize auth service
    auth_service = AuthService(db_path=args.db_path)

    print(f"🔧 Stock Agent Admin Tool")
    print(f"📁 Database: {args.db_path}")
    print()

    # Execute commands
    if args.command == 'create-user':
        password = args.password
        if not password:
            password = getpass.getpass("Enter password: ")
            password_confirm = getpass.getpass("Confirm password: ")
            if password != password_confirm:
                print("❌ Passwords do not match")
                sys.exit(1)

        success = create_user(args.email, password, args.username, auth_service)
        sys.exit(0 if success else 1)

    elif args.command == 'list-users':
        list_users(auth_service)

    elif args.command == 'test-notification':
        success = test_notification(args.topic, args.ticker)
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
