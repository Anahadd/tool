# 🔥 Firebase Security Rules - UPDATE REQUIRED

## New Rules for User Sheets

Add these rules to your Firebase Console:

### **Firestore Rules** (Database → Rules):

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
    
    // User sheets - NEW!
    match /user_sheets/{sheetId} {
      allow read, write, delete: if request.auth != null && request.resource.data.user_id == request.auth.uid;
      allow create: if request.auth != null && request.resource.data.user_id == request.auth.uid;
    }
  }
}
```

### **Storage Rules** (Storage → Rules):

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

## How to Apply:

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: **kalshitool**
3. Go to **Firestore Database** → **Rules** tab
4. Replace with the Firestore rules above
5. Click **Publish**
6. Go to **Storage** → **Rules** tab
7. Replace with the Storage rules above
8. Click **Publish**

**⚠️ Important:** Without these rules, users won't be able to create/edit sheets in the dashboard!

