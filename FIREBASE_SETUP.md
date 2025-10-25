# 🔥 Firebase Setup Guide

Complete guide for setting up Firebase for the Impressions Tool.

## 📋 What Firebase Provides

- **Authentication**: User login/signup
- **Firestore**: Store user preferences (default sheet URL, settings)
- **Storage**: Store credentials.json files securely
- **Per-user isolation**: Each user's data is completely separate

---

## 🚀 Setup Steps

### 1. Create Firebase Project

1. Go to https://console.firebase.google.com/
2. Click **"Add project"**
3. Project name: `impressions-tool`
4. Enable Google Analytics (optional)
5. Click **"Create project"**

---

### 2. Enable Authentication

1. Click **"Authentication"** → **"Get started"**
2. Click **"Sign-in method"** tab
3. Enable **"Email/Password"**:
   - Toggle "Enable"
   - Click "Save"

---

### 3. Set Up Firestore Database

1. Click **"Firestore Database"** → **"Create database"**
2. Select **"Production mode"**
3. Choose location (e.g., `us-central1`)
4. Click **"Enable"**

5. **Add Security Rules**:
   - Click "Rules" tab
   - Paste this:
   ```javascript
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       // Users collection - only owner can access
       match /users/{userId} {
         allow read, write: if request.auth != null && request.auth.uid == userId;
       }
       
       // User credentials - only owner can access
       match /user_credentials/{userId} {
         allow read, write: if request.auth != null && request.auth.uid == userId;
       }
     }
   }
   ```
   - Click "Publish"

---

### 4. Set Up Storage

1. Click **"Storage"** → **"Get started"**
2. Select **"Production mode"**
3. Choose same location as Firestore
4. Click **"Done"**

5. **Add Security Rules**:
   - Click "Rules" tab
   - Paste this:
   ```javascript
   rules_version = '2';
   service firebase.storage {
     match /b/{bucket}/o {
       // Credentials folder - only owner can access
       match /credentials/{userId}/{allPaths=**} {
         allow read, write: if request.auth != null && request.auth.uid == userId;
       }
     }
   }
   ```
   - Click "Publish"

---

### 5. Get Web App Config (for Frontend)

1. Click ⚙️ → **"Project settings"**
2. Scroll to **"Your apps"**
3. Click **</>** (Web icon)
4. App nickname: `impressions-tool-web`
5. Click **"Register app"**
6. **Copy the firebaseConfig object**:
   ```javascript
   const firebaseConfig = {
     apiKey: "AIzaSy...",
     authDomain: "your-project.firebaseapp.com",
     projectId: "your-project-id",
     storageBucket: "your-project.appspot.com",
     messagingSenderId: "123456789",
     appId: "1:123:web:abc..."
   };
   ```
7. Save this - you'll add it to your frontend

---

### 6. Get Service Account Key (for Backend)

1. Still in **"Project settings"**
2. Click **"Service accounts"** tab
3. Click **"Generate new private key"**
4. Click **"Generate key"** (downloads JSON file)
5. **Save this file securely!**

For Railway deployment, you'll add this as an environment variable.

---

## 🔧 Configuration for Production

### Railway Environment Variables

Add these in your Railway dashboard:

```bash
# Firebase Service Account (entire JSON content, minified)
FIREBASE_SERVICE_ACCOUNT={"type":"service_account","project_id":"...","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}

# Firebase Storage Bucket
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
```

**To minify the JSON**:
```bash
cat serviceAccountKey.json | jq -c
```

Or just copy the entire file content as one line.

---

## 🎯 User Flow After Setup

### First Time:
1. User creates account (email/password)
2. User uploads `credentials.json` → **Saved to Firebase Storage**
3. User connects to Google Sheets (OAuth) → **Token saved to Firestore**
4. User enters Sheet URL and clicks "Save as Default" → **Saved to Firestore**

### Every Time After:
1. User logs in
2. Clicks "Run Update"
3. ✅ **Done!** (credentials and sheet URL auto-loaded from Firebase)

---

## 🔒 Security Features

✅ Each user's credentials are in their own Storage folder  
✅ Firestore rules prevent users from accessing each other's data  
✅ Firebase Authentication handles password hashing & security  
✅ Service Account Key only accessible to backend (Railway)  
✅ Frontend only gets user-specific data after authentication  

---

## 📊 Data Structure

### Firestore Collections

#### `users/{userId}`
```json
{
  "email": "user@example.com",
  "username": "john_doe",
  "created_at": "2025-01-20T10:30:00Z",
  "last_login": "2025-01-20T10:30:00Z",
  "preferences": {
    "spreadsheet_url": "https://docs.google.com/spreadsheets/d/...",
    "worksheet_name": "Sheet1",
    "updated_at": "2025-01-20T10:30:00Z"
  }
}
```

#### `user_credentials/{userId}`
```json
{
  "has_credentials": true,
  "filename": "credentials.json",
  "uploaded_at": "2025-01-20T10:30:00Z",
  "storage_path": "credentials/{userId}/credentials.json",
  "oauth_token": "{ ... OAuth token JSON ... }",
  "oauth_updated_at": "2025-01-20T10:30:00Z"
}
```

### Storage Structure

```
credentials/
  {userId}/
    credentials.json
```

---

## 🧪 Testing Locally

1. Download your Service Account JSON file
2. Set environment variable:
   ```bash
   export FIREBASE_SERVICE_ACCOUNT="/path/to/serviceAccountKey.json"
   export FIREBASE_STORAGE_BUCKET="your-project-id.appspot.com"
   ```
3. Run the app:
   ```bash
   python web_app.py
   ```

---

## ✅ Verification Checklist

- [ ] Firebase project created
- [ ] Authentication enabled (Email/Password)
- [ ] Firestore database created with security rules
- [ ] Storage enabled with security rules
- [ ] Web app registered and config copied
- [ ] Service Account key generated and saved
- [ ] Environment variables set in Railway

---

## 🆘 Troubleshooting

### "Firebase not initialized"
- Check `FIREBASE_SERVICE_ACCOUNT` is set correctly
- Verify the JSON format is valid
- Check `FIREBASE_STORAGE_BUCKET` matches your project

### "Permission denied" errors
- Verify Firestore security rules are published
- Verify Storage security rules are published
- Check user is authenticated before making requests

### Storage upload fails
- Ensure bucket name is correct in env vars
- Check Storage is enabled in Firebase Console
- Verify user has authentication token

---

## 📚 Next Steps

After completing this setup:
1. Update your frontend with Firebase config
2. Add the Firebase SDK to your web app
3. Deploy to Railway with environment variables
4. Test the authentication flow
5. Test credential upload and retrieval

