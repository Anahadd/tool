# CRITICAL: Firestore Security Rules Required!

## The Issue

If sheets aren't saving or loading, it's because Firestore Security Rules aren't set up yet!

## SOLUTION (1 minute)

### Steps:

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: **kalshitool**
3. Click **Firestore Database** in left sidebar
4. Click **Rules** tab at the top
5. **Replace everything** with these rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // User profiles
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // User credentials and OAuth tokens
    match /user_credentials/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // User sheets - CRITICAL!
    match /user_sheets/{sheetId} {
      // Allow users to read their own sheets
      allow read: if request.auth != null && resource.data.user_id == request.auth.uid;
      
      // Allow users to create sheets (must set user_id to their own uid)
      allow create: if request.auth != null && request.resource.data.user_id == request.auth.uid;
      
      // Allow users to update/delete their own sheets
      allow update, delete: if request.auth != null && resource.data.user_id == request.auth.uid;
    }
  }
}
```

6. Click **"Publish"** button

### That's it!

Now sheets will save and load correctly.

---

## Storage Rules Too

Also go to **Storage** → **Rules** and add:

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /credentials/{userId}/{allPaths=**} {
      allow read, write, delete: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

Click **"Publish"**

---

## Why This Is Required

Firebase requires explicit security rules for every collection. Without these rules:
- Sheets won't save (permission denied)
- Sheets won't load (permission denied)
- Credentials won't upload (permission denied)

**This is a one-time setup!**
