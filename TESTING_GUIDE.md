# 🧪 Firebase Integration Testing Guide

## ✅ What's Been Implemented

### Backend (web_app.py)
- ✅ Firebase ID token verification for API authentication
- ✅ Retrieve `credentials.json` from Firebase Storage (per-user)
- ✅ OAuth flow saves tokens to Firestore (per-user)
- ✅ Load OAuth tokens from Firestore on subsequent requests
- ✅ All API endpoints secured with Firebase authentication

### Frontend (static/)
- ✅ Firebase SDK initialized (Auth, Firestore, Storage)
- ✅ Login/Register with email+password
- ✅ Forgot password (email reset link)
- ✅ Upload `credentials.json` → Saved to Firebase Storage
- ✅ Delete credentials button
- ✅ Save defaults (sheet URL) → Saved to Firestore
- ✅ Clear defaults button
- ✅ Auto-login (Firebase session persistence)
- ✅ All API calls include Firebase ID token in Authorization header

### User Flow
1. **First Time User:**
   - Open app → See login modal
   - Click "Create account"
   - Enter email, username, password → Account created
   - Auto-logged in forever (Firebase session)
   - Upload `credentials.json` → Saved to Firebase Storage
   - Click "Connect to Google Sheets" → OAuth flow
   - Enter Sheet URL → Works immediately
   - Click "Save as Defaults" → Saved to Firestore

2. **Returning User:**
   - Open app → Auto-logged in (no modal)
   - Credentials auto-loaded from Firebase
   - Sheet URL auto-filled from Firestore
   - Just click "Run Update" → Done!

---

## 🧪 Manual Testing Steps

### Test 1: User Registration ✓
```
1. Open http://localhost:8000
2. Should see auth modal
3. Click "Create one" link
4. Fill form:
   - Username: testuser
   - Email: test@example.com
   - Password: password123
5. Click "Create Account"
6. Should see success message
7. Modal should close automatically
```

### Test 2: Credentials Upload ✓
```
1. Prepare a valid credentials.json file
2. Drag and drop on the upload zone
3. Should see "✓ Credentials saved to your account!"
4. Green status box should appear: "✓ Credentials saved to your account"
5. "Connect to Google Sheets" button should enable
```

### Test 3: OAuth Flow ✓
```
1. Click "Connect to Google Sheets"
2. Popup window opens with Google OAuth
3. Sign in and grant permissions
4. Popup closes automatically
5. Should see "✓ Google Sheets connected successfully!"
```

### Test 4: Save Defaults ✓
```
1. Paste a Google Sheets URL
2. Enter worksheet name (default: Sheet1)
3. Click "Save as Defaults"
4. Should see "✓ Defaults saved! They will auto-load next time."
5. "Clear Defaults" button should appear
```

### Test 5: Run Update ✓
```
1. With everything configured above
2. Click "Run Update"
3. Should see "Fetching stats from TikTok, YouTube, and Instagram..."
4. Sheet should update with latest stats
5. Should see "✓ Sheet updated successfully!"
```

### Test 6: Auto-Login & Persistence ✓
```
1. Refresh the page (⌘R / Ctrl+R)
2. Should NOT see login modal
3. Should see "Welcome back, [email]!"
4. Should see "✓ Credentials loaded from your account"
5. Sheet URL should be pre-filled (if saved as default)
6. Everything ready to use immediately
```

### Test 7: Delete Credentials ✓
```
1. Click "Delete Saved Credentials" button
2. Confirm the dialog
3. Should see "✓ Credentials deleted"
4. Upload zone should reset
5. Will need to re-upload credentials.json
```

### Test 8: Clear Defaults ✓
```
1. Click "Clear Defaults" button
2. Confirm the dialog
3. Sheet URL should be cleared
4. "Clear Defaults" button should hide
```

---

## 🔧 Environment Variables for Production

Create a `.env` file or set environment variables:

```bash
FIREBASE_SERVICE_ACCOUNT=/path/to/kalshitool-firebase-adminsdk-fbsvc-99ead06106.json
FIREBASE_STORAGE_BUCKET=kalshitool.firebasestorage.app

# Optional
YOUTUBE_API_KEY=your-youtube-api-key
APIFY_TOKEN=your-apify-token
BASE_URL=https://your-domain.com
```

---

## 🚀 Deployment Checklist

### Railway Deployment:
1. Add environment variables in Railway dashboard:
   - `FIREBASE_SERVICE_ACCOUNT` (paste entire JSON content)
   - `FIREBASE_STORAGE_BUCKET=kalshitool.firebasestorage.app`
   - `YOUTUBE_API_KEY`
   - `APIFY_TOKEN`
   - `BASE_URL=https://your-app.up.railway.app`

2. Deploy: `git push origin main`

3. Railway will automatically deploy from GitHub

### Firebase Security Rules:

**Firestore Rules:**
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    match /user_credentials/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

**Storage Rules:**
```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /credentials/{userId}/{allPaths=**} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

---

## ✅ Status: READY FOR PRODUCTION

All features implemented and tested locally. Ready to deploy!
