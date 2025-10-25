# Fix: redirect_uri_mismatch Error

## The Problem

OAuth is working, but Google is rejecting the redirect URI:
```
Error 400: redirect_uri_mismatch
```

This means `http://localhost:8000/api/oauth-callback` is not authorized in your Google Cloud Console.

---

## SOLUTION (2 minutes)

### Step 1: Open Google Cloud Console

1. Go to: https://console.cloud.google.com/
2. Select your project (the one in your `credentials.json`)

### Step 2: Go to OAuth Consent Screen

1. Click **APIs & Services** in left sidebar
2. Click **OAuth consent screen**
3. Verify your app name shows up

### Step 3: Configure Authorized Redirect URIs

1. Click **Credentials** in left sidebar
2. Find your **OAuth 2.0 Client ID** (Web application)
3. Click on it to edit
4. Scroll to **"Authorized redirect URIs"**
5. Click **"+ ADD URI"**
6. Add these URIs:

```
http://localhost:8000/api/oauth-callback
http://127.0.0.1:8000/api/oauth-callback
```

7. Click **"SAVE"** at the bottom

---

## For Production Later

When deploying to Railway/Heroku, also add:
```
https://your-domain.com/api/oauth-callback
```

---

## After Adding URIs

1. Wait 5-10 seconds for Google to propagate changes
2. Go back to http://localhost:8000
3. Click Settings → Connect to Google Sheets
4. OAuth popup will open
5. Complete authorization
6. **It will work!** ✅

---

## Verify It Worked

After completing OAuth:
- You'll see: "Google Sheets connected successfully!"
- Settings modal will show: ✓ Connected
- You can then click "RUN UPDATE" on any sheet

---

## Alternative: Download New credentials.json

If you can't find the OAuth client:

1. Go to APIs & Services → Credentials
2. Create new OAuth 2.0 Client ID
3. Application type: **Web application**
4. Add redirect URIs as shown above
5. Download the new credentials.json
6. Upload it in the app (Settings → Upload New Credentials)

---

This is a **one-time setup** for each environment (local, staging, production).

