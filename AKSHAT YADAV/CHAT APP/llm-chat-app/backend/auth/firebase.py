import os
import json
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, status

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirebaseAuth:
    """Firebase authentication manager"""
    
    def __init__(self):
        self.app = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                # Try to get service account key from environment
                service_account_key = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
                
                if service_account_key:
                    # Parse service account key from environment variable
                    service_account_info = json.loads(service_account_key)
                    cred = credentials.Certificate(service_account_info)
                else:
                    # Try to load from file
                    service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'firebase-service-account.json')
                    if os.path.exists(service_account_path):
                        cred = credentials.Certificate(service_account_path)
                    else:
                        # Use default credentials (for Google Cloud environments)
                        cred = credentials.ApplicationDefault()
                
                # Initialize Firebase app
                self.app = firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully")
            else:
                self.app = firebase_admin.get_app()
                logger.info("Using existing Firebase Admin SDK instance")
                
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
            logger.warning("Firebase authentication will not be available")
    
    def verify_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Firebase ID token and return user information
        
        Args:
            id_token: Firebase ID token from client
            
        Returns:
            Dictionary containing user information or None if verification fails
        """
        if not self.app:
            logger.error("Firebase not initialized")
            return None
            
        try:
            # Verify the ID token
            decoded_token = auth.verify_id_token(id_token)
            
            user_info = {
                'uid': decoded_token.get('uid'),
                'email': decoded_token.get('email'),
                'name': decoded_token.get('name', decoded_token.get('email', 'Unknown')),
                'email_verified': decoded_token.get('email_verified', False),
                'firebase_claims': decoded_token
            }
            
            logger.info(f"Token verified successfully for user: {user_info['email']}")
            return user_info
            
        except auth.ExpiredIdTokenError:
            logger.warning("ID token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except auth.RevokedIdTokenError:
            logger.warning("ID token has been revoked")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        except auth.InvalidIdTokenError:
            logger.warning("Invalid ID token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed"
            )
    
    def get_user_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """
        Get user information by Firebase UID
        
        Args:
            uid: Firebase user UID
            
        Returns:
            Dictionary containing user information or None if not found
        """
        if not self.app:
            logger.error("Firebase not initialized")
            return None
            
        try:
            user_record = auth.get_user(uid)
            
            user_info = {
                'uid': user_record.uid,
                'email': user_record.email,
                'name': user_record.display_name or user_record.email or 'Unknown',
                'email_verified': user_record.email_verified,
                'created_at': user_record.user_metadata.creation_timestamp,
                'last_sign_in': user_record.user_metadata.last_sign_in_timestamp
            }
            
            return user_info
            
        except auth.UserNotFoundError:
            logger.warning(f"User not found: {uid}")
            return None
        except Exception as e:
            logger.error(f"Failed to get user by UID: {e}")
            return None
    
    def create_custom_token(self, uid: str, additional_claims: Optional[Dict] = None) -> Optional[str]:
        """
        Create a custom token for a user
        
        Args:
            uid: Firebase user UID
            additional_claims: Additional claims to include in the token
            
        Returns:
            Custom token string or None if creation fails
        """
        if not self.app:
            logger.error("Firebase not initialized")
            return None
            
        try:
            custom_token = auth.create_custom_token(uid, additional_claims)
            return custom_token.decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to create custom token: {e}")
            return None

# Global Firebase auth instance
firebase_auth = FirebaseAuth()

def verify_firebase_token(id_token: str) -> Dict[str, Any]:
    """
    Convenience function to verify Firebase token
    
    Args:
        id_token: Firebase ID token
        
    Returns:
        User information dictionary
        
    Raises:
        HTTPException: If token verification fails
    """
    user_info = firebase_auth.verify_token(id_token)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )
    return user_info

def get_firebase_user(uid: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get user by UID
    
    Args:
        uid: Firebase user UID
        
    Returns:
        User information dictionary or None
    """
    return firebase_auth.get_user_by_uid(uid)

def create_firebase_custom_token(uid: str, claims: Optional[Dict] = None) -> Optional[str]:
    """
    Convenience function to create custom token
    
    Args:
        uid: Firebase user UID
        claims: Additional claims
        
    Returns:
        Custom token string or None
    """
    return firebase_auth.create_custom_token(uid, claims)

# Mock authentication for development (when Firebase is not available)
def mock_verify_token(id_token: str) -> Dict[str, Any]:
    """
    Mock token verification for development
    """
    if id_token == "mock_token":
        return {
            'uid': 'mock_user_123',
            'email': 'test@example.com',
            'name': 'Test User',
            'email_verified': True,
            'firebase_claims': {}
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid mock token"
        )

if __name__ == "__main__":
    # Test Firebase initialization
    print("Testing Firebase authentication...")
    if firebase_auth.app:
        print("✅ Firebase initialized successfully!")
    else:
        print("❌ Firebase initialization failed!")
