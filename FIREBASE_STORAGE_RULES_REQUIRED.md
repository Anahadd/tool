# CRITICAL: Firebase Storage Rules Required!

## The Problem

Credentials upload is failing because **Firebase Storage rules aren't set up**!

When you upload `credentials.json`, Firebase blocks it with permission denied.

---

## SOLUTION (1 minute)

### Go to Firebase Console:

1. Open https://console.firebase.google.com/
2. Select project: **kalshitool**
3. Click **Storage** in left sidebar
4. Click **Rules** tab at the top
5. **Replace everything** with these rules:

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Allow users to read/write their own credentials
    match /credentials/{userId}/{allPaths=**} {
      allow read, write, delete: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

6. Click **"Publish"** button

---

## Why This Is Required

Firebase Storage requires explicit security rules. Without these rules:
- ❌ File upload fails (permission denied)
- ❌ OAuth can't read credentials from storage
- ❌ "Connect to Google Sheets" fails

**This is a one-time setup!**

---

## After Adding Rules

1. Refresh http://localhost:8000
2. Upload `credentials.json` again
3. Click "Connect to Google Sheets"
4. It will work! ✅

---

## To Verify Rules Are Set

After publishing rules, run this test:
```bash
# Upload should work without errors
```

The error message will change from:
- ❌ "Permission denied" 
- ✅ "OAuth URL generated successfully"

