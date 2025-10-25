# 🔥 Firebase Authentication Setup - REQUIRED

## ⚠️ THE ISSUE

You're getting `auth/invalid-credential` because:
1. **No account exists yet** - Firebase shows 0 users in database
2. **Email/Password provider might not be enabled**

## ✅ SOLUTION - Enable Email/Password Authentication

### Steps:

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: **kalshitool**
3. Click **Authentication** in left sidebar
4. Click **Sign-in method** tab
5. Find **Email/Password** in the list
6. Click on it
7. **Toggle "Enable"** to ON
8. Click **Save**

### Screenshot Guide:
```
Authentication > Sign-in method

Providers:
┌─────────────────────────────────────────┐
│ Email/Password              [Toggle ON] │  ← Make sure this is ENABLED
│ Phone                       [Toggle]    │
│ Google                      [Toggle]    │
│ ...                                     │
└─────────────────────────────────────────┘
```

## 🧪 After Enabling:

1. Refresh http://localhost:8000
2. Click **"Create one"** link
3. Fill in:
   - Username: anything you want
   - Email: your email
   - Password: at least 6 characters
4. Click **"Create Account"**
5. You'll be auto-logged in!
6. Now you can sign in anytime with those credentials

## 💡 Why This Happens:

Firebase Authentication requires you to explicitly enable each sign-in method:
- Email/Password
- Google
- Facebook
- etc.

By default, they're all **disabled** for security.

---

**Once enabled, your sign-in will work perfectly!**
