#!/usr/bin/env python3
"""
Stock Agent Admin CLI Tool

This tool allows administrators to manage users in the stock agent system.
"""

import argparse
import getpass
import sys
from typing import Optional

from ..auth import AuthService


def create_user(auth_service: AuthService, username: str, email: str, password: Optional[str] = None) -> bool:
    """Create a new user"""
    if not password:
        password = getpass.getpass("Enter password for new user: ")
        confirm_password = getpass.getpass("Confirm password: ")
        
        if password != confirm_password:
            print("❌ Passwords do not match!")
            return False
    
    try:
        user = auth_service.register_user(username, email, password)
        if user:
            print(f"✅ User '{username}' created successfully!")
            print(f"   Email: {email}")
            print(f"   User ID: {user.id}")
            return True
        else:
            print(f"❌ Failed to create user '{username}' - username or email already exists")
            return False
    except ValueError as e:
        print(f"❌ Error creating user: {e}")
        return False


def list_users(auth_service: AuthService):
    """List all users in the system"""
    import sqlite3
    
    try:
        with sqlite3.connect(auth_service.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, username, email, created_at, is_active 
                FROM users 
                ORDER BY created_at DESC
            """)
            users = cursor.fetchall()
            
            if not users:
                print("No users found in the system.")
                return
            
            print("\n📋 User List:")
            print("-" * 80)
            print(f"{'ID':<4} {'Username':<20} {'Email':<30} {'Created':<20} {'Active':<6}")
            print("-" * 80)
            
            for user in users:
                user_id, username, email, created_at, is_active = user
                status = "✅" if is_active else "❌"
                created_str = created_at[:19] if created_at else "Unknown"
                print(f"{user_id:<4} {username:<20} {email:<30} {created_str:<20} {status:<6}")
            
            print("-" * 80)
            print(f"Total users: {len(users)}")
            
    except Exception as e:
        print(f"❌ Error listing users: {e}")


def deactivate_user(auth_service: AuthService, username: str) -> bool:
    """Deactivate a user account"""
    import sqlite3
    
    try:
        with sqlite3.connect(auth_service.db_path) as conn:
            cursor = conn.execute("SELECT id FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            
            if not user:
                print(f"❌ User '{username}' not found")
                return False
            
            conn.execute("UPDATE users SET is_active = 0 WHERE username = ?", (username,))
            conn.commit()
            
            print(f"✅ User '{username}' has been deactivated")
            return True
            
    except Exception as e:
        print(f"❌ Error deactivating user: {e}")
        return False


def activate_user(auth_service: AuthService, username: str) -> bool:
    """Activate a user account"""
    import sqlite3
    
    try:
        with sqlite3.connect(auth_service.db_path) as conn:
            cursor = conn.execute("SELECT id FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            
            if not user:
                print(f"❌ User '{username}' not found")
                return False
            
            conn.execute("UPDATE users SET is_active = 1 WHERE username = ?", (username,))
            conn.commit()
            
            print(f"✅ User '{username}' has been activated")
            return True
            
    except Exception as e:
        print(f"❌ Error activating user: {e}")
        return False


def reset_password(auth_service: AuthService, username: str) -> bool:
    """Reset a user's password"""
    import sqlite3
    
    try:
        with sqlite3.connect(auth_service.db_path) as conn:
            cursor = conn.execute("SELECT id FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            
            if not user:
                print(f"❌ User '{username}' not found")
                return False
            
            new_password = getpass.getpass(f"Enter new password for '{username}': ")
            confirm_password = getpass.getpass("Confirm new password: ")
            
            if new_password != confirm_password:
                print("❌ Passwords do not match!")
                return False
            
            if len(new_password) < 8:
                print("❌ Password must be at least 8 characters long")
                return False
            
            password_hash = auth_service._hash_password(new_password)
            conn.execute("UPDATE users SET password_hash = ? WHERE username = ?", (password_hash, username))
            conn.commit()
            
            print(f"✅ Password reset successfully for user '{username}'")
            return True
            
    except Exception as e:
        print(f"❌ Error resetting password: {e}")
        return False


def main():
    """Main CLI entry point"""
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
        success = create_user(auth_service, args.username, args.email, args.password)
        sys.exit(0 if success else 1)
        
    elif args.command == 'list-users':
        list_users(auth_service)
        
    elif args.command == 'deactivate-user':
        success = deactivate_user(auth_service, args.username)
        sys.exit(0 if success else 1)
        
    elif args.command == 'activate-user':
        success = activate_user(auth_service, args.username)
        sys.exit(0 if success else 1)
        
    elif args.command == 'reset-password':
        success = reset_password(auth_service, args.username)
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
