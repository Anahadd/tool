# Firebase Complete Setup Checklist

Do these 4 things in Firebase Console to make everything work!

---

## Step 1: Enable Google Sign-In Provider

1. Go to https://console.firebase.google.com/
2. Select project: **kalshitool**
3. Click **Authentication** → **Sign-in method** tab
4. Find **"Google"** in the providers list
5. Click on it
6. Toggle **"Enable"** to ON
7. Set **Support email** (your email address)
8. Click **"Save"**

---

## Step 2: Add Authorized Domains

**Still in Authentication:**

1. Click **"Settings"** tab (at the top)
2. Scroll to **"Authorized domains"** section
3. Click **"Add domain"** button
4. Enter: `localhost`
5. Click **"Add"**

**For production later:** Also add your Railway domain when deploying

---

## Step 3: Add Firestore Security Rules

1. Click **Firestore Database** in left sidebar
2. Click **"Rules"** tab at the top
3. **Replace everything** with:

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
    
    match /user_sheets/{sheetId} {
      allow read: if request.auth != null && resource.data.user_id == request.auth.uid;
      allow create: if request.auth != null && request.resource.data.user_id == request.auth.uid;
      allow update, delete: if request.auth != null && resource.data.user_id == request.auth.uid;
    }
  }
}
```

4. Click **"Publish"**

---

## Step 4: Add Storage Security Rules

1. Click **Storage** in left sidebar
2. Click **"Rules"** tab at the top
3. **Replace everything** with:

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

4. Click **"Publish"**

---

## Test Everything Works!

1. Refresh http://localhost:8000
2. Click "Sign in with Google"
3. Select your Google account
4. Upload credentials.json
5. OAuth popup opens → Complete authorization
6. Dashboard loads
7. Click "+ Add Google Sheets"
8. Fill in Name, URL, Description
9. Click "Save"
10. Sheet appears in table with "RUN UPDATE" button

Everything should work perfectly now!

---

## Troubleshooting

If you still get errors, check browser console (F12) and look for:
- `auth/unauthorized-domain` → Add localhost to authorized domains
- `permission-denied` → Add Firestore/Storage rules
- Other errors → Share them with me!

---

## Summary

These 4 steps enable:
- Google Sign-In authentication
- Localhost development
- Firestore database operations (save/load sheets)
- Storage operations (upload credentials)

**Do all 4 steps and everything will work!**

