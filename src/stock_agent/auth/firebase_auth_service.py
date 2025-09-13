import os
import json
from typing import Optional, Dict, Any
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from .models import User
from .auth_service import AuthService


class FirebaseAuthService:
    """Firebase Authentication service for validating ID tokens and managing users"""
    
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK if not already initialized"""
        if not firebase_admin._apps:
            try:
                # Try to load from service account file
                creds_path = os.getenv('FIREBASE_CREDS_PATH')
                if creds_path and os.path.exists(creds_path):
                    cred = credentials.Certificate(creds_path)
                else:
                    # Try to load from environment variable (JSON string)
                    service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
                    if service_account_json:
                        service_account_info = json.loads(service_account_json)
                        cred = credentials.Certificate(service_account_info)
                    else:
                        # Use default credentials (for Google Cloud environments)
                        cred = credentials.ApplicationDefault()
                
                firebase_admin.initialize_app(cred)
                print("Firebase Admin SDK initialized successfully")
            except Exception as e:
                print(f"Failed to initialize Firebase Admin SDK: {e}")
                raise
    
    def verify_firebase_id_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Firebase ID token and return decoded claims
        
        Args:
            id_token: Firebase ID token to verify
            
        Returns:
            Dictionary with user claims if valid, None if invalid
        """
        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
            return {
                'uid': decoded_token['uid'],
                'email': decoded_token.get('email'),
                'email_verified': decoded_token.get('email_verified', False),
                'name': decoded_token.get('name'),
                'picture': decoded_token.get('picture'),
                'provider_id': decoded_token.get('firebase', {}).get('sign_in_provider'),
                'auth_time': decoded_token.get('auth_time'),
                'exp': decoded_token.get('exp'),
                'iat': decoded_token.get('iat'),
                'firebase_claims': decoded_token
            }
        except firebase_auth.InvalidIdTokenError:
            print("Invalid Firebase ID token")
            return None
        except firebase_auth.ExpiredIdTokenError:
            print("Expired Firebase ID token")
            return None
        except firebase_auth.RevokedIdTokenError:
            print("Revoked Firebase ID token")
            return None
        except Exception as e:
            print(f"Firebase token verification error: {e}")
            return None
    
    def get_or_create_user_from_firebase(self, firebase_claims: Dict[str, Any]) -> Optional[User]:
        """
        Get existing user or create new user from Firebase claims
        
        Args:
            firebase_claims: Decoded Firebase token claims
            
        Returns:
            User object if successful, None if failed
        """
        firebase_uid = firebase_claims['uid']
        email = firebase_claims.get('email')
        
        if not email:
            print(f"No email found in Firebase claims for UID: {firebase_uid}")
            return None
        
        # Try to find existing user by email
        user = self._find_user_by_email(email)
        
        if not user:
            # Create new user from Firebase data
            user = self._create_user_from_firebase(firebase_claims)
        
        return user
    
    def _find_user_by_email(self, email: str) -> Optional[User]:
        """Find user by email in local database"""
        import sqlite3
        
        try:
            with sqlite3.connect(self.auth_service.db_path) as conn:
                cursor = conn.execute(
                    "SELECT id, username, email, password_hash, created_at, is_active "
                    "FROM users WHERE email = ? AND is_active = 1",
                    (email,)
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
        except Exception as e:
            print(f"Error finding user by email: {e}")
        
        return None
    
    def _create_user_from_firebase(self, firebase_claims: Dict[str, Any]) -> Optional[User]:
        """Create new user from Firebase claims"""
        try:
            email = firebase_claims['email']
            name = firebase_claims.get('name', '')
            
            # Generate username from email or name
            username = self._generate_username(email, name)
            
            # Create user with a placeholder password (Firebase handles auth)
            user = self.auth_service.register_user(
                username=username,
                email=email,
                password="firebase_managed_auth"  # Placeholder - not used for Firebase users
            )
            
            if user:
                print(f"Created new user from Firebase: {email}")
            
            return user
            
        except Exception as e:
            print(f"Error creating user from Firebase claims: {e}")
            return None
    
    def _generate_username(self, email: str, name: str = "") -> str:
        """Generate unique username from email or name"""
        if name:
            # Use name if available, clean it up
            username = name.lower().replace(' ', '_').replace('.', '_')
            username = ''.join(c for c in username if c.isalnum() or c == '_')
        else:
            # Use email prefix
            username = email.split('@')[0].lower()
            username = ''.join(c for c in username if c.isalnum() or c == '_')
        
        # Ensure uniqueness by checking database
        original_username = username
        counter = 1
        
        while self._username_exists(username):
            username = f"{original_username}_{counter}"
            counter += 1
        
        return username
    
    def _username_exists(self, username: str) -> bool:
        """Check if username already exists"""
        import sqlite3
        
        try:
            with sqlite3.connect(self.auth_service.db_path) as conn:
                cursor = conn.execute(
                    "SELECT 1 FROM users WHERE username = ?",
                    (username,)
                )
                return cursor.fetchone() is not None
        except Exception:
            return False
    
    def get_user_from_firebase_token(self, id_token: str) -> Optional[User]:
        """
        Complete flow: verify token and get/create user
        
        Args:
            id_token: Firebase ID token
            
        Returns:
            User object if authentication successful, None otherwise
        """
        firebase_claims = self.verify_firebase_id_token(id_token)
        if not firebase_claims:
            return None
        
        return self.get_or_create_user_from_firebase(firebase_claims)