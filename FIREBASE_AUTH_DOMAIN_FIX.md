# 🚨 URGENT: Fix "auth/unauthorized-domain" Error

## The Problem

Firebase is blocking sign-in because `localhost:8000` is not in the authorized domains list.

## SOLUTION (Takes 30 seconds)

### Steps:

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: **kalshitool**
3. Click **Authentication** in left sidebar
4. Click **Settings** tab (top of page)
5. Scroll down to **Authorized domains** section
6. You'll see domains like:
   - kalshitool.firebaseapp.com
   - kalshitool.web.app
7. Click **"Add domain"** button
8. Enter: `localhost`
9. Click **"Add"**

### That's it!

Now refresh http://localhost:8000 and try signing in again.

---

## For Production Deployment:

When you deploy to Railway, also add your Railway domain:
1. Click "Add domain" again
2. Enter your Railway URL (e.g., `your-app.up.railway.app`)
3. Click "Add"

---

## Why This Happens:

Firebase Authentication only allows sign-in from pre-approved domains for security. By default, only Firebase's own domains are allowed. You must explicitly add `localhost` for local development.

**This is a one-time setup!**

