"""
Firebase service layer for user authentication and data storage
"""
import os
import json
import base64
from typing import Optional, Dict, Any, Tuple
from firebase_admin import auth, firestore, storage
from datetime import datetime
import firebase_config

def create_user(email: str, password: str, username: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    Create a new user in Firebase Auth and Firestore
    
    Returns:
        (success, message, user_data)
    """
    try:
        # Create user in Firebase Auth
        user = auth.create_user(
            email=email,
            password=password,
            display_name=username
        )
        
        # Store additional user data in Firestore
        db = firebase_config.get_firestore()
        if db:
            user_ref = db.collection('users').document(user.uid)
            user_data = {
                'email': email,
                'username': username,
                'created_at': datetime.utcnow(),
                'last_login': datetime.utcnow()
            }
            user_ref.set(user_data)
        
        return True, "User created successfully", {
            'uid': user.uid,
            'email': email,
            'username': username
        }
        
    except auth.EmailAlreadyExistsError:
        return False, "Email already registered", None
    except Exception as e:
        return False, f"Error creating user: {str(e)}", None

def verify_user(email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    Verify user credentials
    Note: Firebase Admin SDK doesn't directly verify passwords.
    This should be done on the client side with Firebase JS SDK.
    
    For server-side, we'll use custom tokens.
    """
    try:
        # Get user by email
        user = auth.get_user_by_email(email)
        
        # Get user data from Firestore
        db = firebase_config.get_firestore()
        if db:
            user_ref = db.collection('users').document(user.uid)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                
                # Update last login
                user_ref.update({'last_login': datetime.utcnow()})
                
                return True, "Login successful", {
                    'uid': user.uid,
                    'email': user.email,
                    'username': user_data.get('username', email.split('@')[0])
                }
        
        return True, "Login successful", {
            'uid': user.uid,
            'email': user.email,
            'username': user.display_name or email.split('@')[0]
        }
        
    except auth.UserNotFoundError:
        return False, "User not found", None
    except Exception as e:
        return False, f"Error verifying user: {str(e)}", None

def create_custom_token(uid: str) -> Optional[str]:
    """Create a custom token for a user"""
    try:
        token = auth.create_custom_token(uid)
        return token.decode('utf-8') if isinstance(token, bytes) else token
    except Exception as e:
        print(f"Error creating custom token: {e}")
        return None

def verify_id_token(id_token: str) -> Optional[Dict]:
    """Verify a Firebase ID token"""
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"Error verifying ID token: {e}")
        return None

def store_credentials(user_id: str, credentials_data: bytes, filename: str = "credentials.json") -> Tuple[bool, str]:
    """
    Store user's Google OAuth credentials in Firebase Storage
    
    Args:
        user_id: Firebase user ID
        credentials_data: Credentials file content (bytes)
        filename: Filename (default: credentials.json)
    
    Returns:
        (success, message)
    """
    try:
        bucket = firebase_config.get_storage()
        if not bucket:
            return False, "Firebase Storage not initialized"
        
        # Store in user-specific path
        blob = bucket.blob(f"credentials/{user_id}/{filename}")
        blob.upload_from_string(
            credentials_data,
            content_type='application/json'
        )
        
        # Also store metadata in Firestore
        db = firebase_config.get_firestore()
        if db:
            cred_ref = db.collection('user_credentials').document(user_id)
            cred_ref.set({
                'has_credentials': True,
                'filename': filename,
                'uploaded_at': datetime.utcnow(),
                'storage_path': f"credentials/{user_id}/{filename}"
            }, merge=True)
        
        return True, "Credentials stored successfully"
        
    except Exception as e:
        return False, f"Error storing credentials: {str(e)}"

def get_credentials(user_id: str, filename: str = "credentials.json") -> Optional[bytes]:
    """
    Retrieve user's Google OAuth credentials from Firebase Storage
    
    Args:
        user_id: Firebase user ID
        filename: Filename (default: credentials.json)
    
    Returns:
        Credentials file content (bytes) or None
    """
    try:
        bucket = firebase_config.get_storage()
        if not bucket:
            return None
        
        blob = bucket.blob(f"credentials/{user_id}/{filename}")
        
        if not blob.exists():
            return None
        
        return blob.download_as_bytes()
        
    except Exception as e:
        print(f"Error retrieving credentials: {e}")
        return None

def has_credentials(user_id: str) -> bool:
    """Check if user has uploaded credentials"""
    try:
        db = firebase_config.get_firestore()
        if not db:
            return False
        
        cred_ref = db.collection('user_credentials').document(user_id)
        cred_doc = cred_ref.get()
        
        if cred_doc.exists:
            data = cred_doc.to_dict()
            return data.get('has_credentials', False)
        
        return False
        
    except Exception as e:
        print(f"Error checking credentials: {e}")
        return False

def store_oauth_token(user_id: str, token_data: str) -> Tuple[bool, str]:
    """
    Store user's OAuth token in Firestore
    
    Args:
        user_id: Firebase user ID
        token_data: OAuth token JSON string
    
    Returns:
        (success, message)
    """
    try:
        db = firebase_config.get_firestore()
        if not db:
            return False, "Firestore not initialized"
        
        cred_ref = db.collection('user_credentials').document(user_id)
        cred_ref.set({
            'oauth_token': token_data,
            'oauth_updated_at': datetime.utcnow()
        }, merge=True)
        
        return True, "OAuth token stored successfully"
        
    except Exception as e:
        return False, f"Error storing OAuth token: {str(e)}"

def get_oauth_token(user_id: str) -> Optional[str]:
    """Retrieve user's OAuth token from Firestore"""
    try:
        db = firebase_config.get_firestore()
        if not db:
            return None
        
        cred_ref = db.collection('user_credentials').document(user_id)
        cred_doc = cred_ref.get()
        
        if cred_doc.exists:
            data = cred_doc.to_dict()
            return data.get('oauth_token')
        
        return None
        
    except Exception as e:
        print(f"Error retrieving OAuth token: {e}")
        return None

def save_user_preferences(user_id: str, preferences: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Save user preferences (default spreadsheet, worksheet, etc.)
    
    Args:
        user_id: Firebase user ID
        preferences: Dict with keys like 'spreadsheet_url', 'worksheet_name', etc.
    
    Returns:
        (success, message)
    """
    try:
        db = firebase_config.get_firestore()
        if not db:
            return False, "Firestore not initialized"
        
        user_ref = db.collection('users').document(user_id)
        preferences['updated_at'] = datetime.utcnow()
        user_ref.set({'preferences': preferences}, merge=True)
        
        return True, "Preferences saved successfully"
        
    except Exception as e:
        return False, f"Error saving preferences: {str(e)}"

def get_user_preferences(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve user preferences"""
    try:
        db = firebase_config.get_firestore()
        if not db:
            return None
        
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            data = user_doc.to_dict()
            return data.get('preferences', {})
        
        return {}
        
    except Exception as e:
        print(f"Error retrieving preferences: {e}")
        return None

def delete_user_data(user_id: str) -> Tuple[bool, str]:
    """Delete all user data (for account deletion)"""
    try:
        # Delete from Firestore
        db = firebase_config.get_firestore()
        if db:
            db.collection('users').document(user_id).delete()
            db.collection('user_credentials').document(user_id).delete()
        
        # Delete from Storage
        bucket = firebase_config.get_storage()
        if bucket:
            blobs = bucket.list_blobs(prefix=f"credentials/{user_id}/")
            for blob in blobs:
                blob.delete()
        
        # Delete from Auth
        auth.delete_user(user_id)
        
        return True, "User data deleted successfully"
        
    except Exception as e:
        return False, f"Error deleting user data: {str(e)}"

