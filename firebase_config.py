"""
Firebase configuration and initialization
"""
import os
import json
import firebase_admin
from firebase_admin import credentials, auth, firestore, storage
from typing import Optional, Dict, Any

# Initialize Firebase Admin SDK
_initialized = False
_db = None
_bucket = None

def init_firebase():
    """Initialize Firebase Admin SDK"""
    global _initialized, _db, _bucket
    
    if _initialized:
        return
    
    try:
        # Get service account key from environment variable
        # Can be either a JSON string or path to JSON file
        service_account = os.getenv("FIREBASE_SERVICE_ACCOUNT")
        
        if not service_account:
            print("⚠️  FIREBASE_SERVICE_ACCOUNT not set. Firebase features disabled.")
            return
        
        # Try to parse as JSON string first
        try:
            service_account_dict = json.loads(service_account)
            cred = credentials.Certificate(service_account_dict)
        except json.JSONDecodeError:
            # If not JSON, treat as file path
            cred = credentials.Certificate(service_account)
        
        # Initialize the app
        firebase_admin.initialize_app(cred, {
            'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET", "")
        })
        
        # Initialize Firestore and Storage
        _db = firestore.client()
        _bucket = storage.bucket()
        
        _initialized = True
        print("✅ Firebase initialized successfully")
        
    except Exception as e:
        print(f"❌ Failed to initialize Firebase: {e}")
        _initialized = False

def get_firestore() -> Optional[Any]:
    """Get Firestore client"""
    if not _initialized:
        init_firebase()
    return _db

def get_storage() -> Optional[Any]:
    """Get Storage bucket"""
    if not _initialized:
        init_firebase()
    return _bucket

def is_firebase_enabled() -> bool:
    """Check if Firebase is properly configured"""
    return _initialized

# Auto-initialize on import
init_firebase()

