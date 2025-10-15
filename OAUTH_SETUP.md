# 🔐 OAuth Setup Guide for Production

## Why This Is Needed

The "Connect to Google Sheets" button uses OAuth2 authentication. For this to work in production, you need to:

1. Configure Google Cloud Console with your production URL
2. Set the `BASE_URL` environment variable

---

## Step 1: Google Cloud Console Setup

### 1.1 Go to Google Cloud Console
- Visit: https://console.cloud.google.com/

### 1.2 Select or Create a Project
- If you already have a project for your OAuth credentials, select it
- Otherwise, create a new project

### 1.3 Enable Required APIs
- Go to "APIs & Services" → "Enabled APIs & services"
- Click "+ ENABLE APIS AND SERVICES"
- Enable:
  - **Google Sheets API**
  - **Google Drive API** (for accessing sheets by name)

### 1.4 Configure OAuth Consent Screen
- Go to "APIs & Services" → "OAuth consent screen"
- Choose "External" (unless you have a Google Workspace)
- Fill in required fields:
  - **App name**: Kalshi Impressions Tool
  - **User support email**: Your email
  - **Developer contact**: Your email
- Add scopes:
  - `https://www.googleapis.com/auth/spreadsheets`
  - `https://www.googleapis.com/auth/drive.readonly`
- Add test users (your email and team members)
- Save and continue

### 1.5 Create OAuth 2.0 Credentials
- Go to "APIs & Services" → "Credentials"
- Click "+ CREATE CREDENTIALS" → "OAuth client ID"
- Choose **"Web application"**
- Set name: "Kalshi Impressions Tool - Production"
- Under **"Authorized redirect URIs"**, add:
  - `https://your-app-name.railway.app/api/oauth-callback`
  - Replace with your actual production URL
  - For local testing: `http://localhost:8000/api/oauth-callback`

### 1.6 Download Credentials
- Click the download button (⬇️) next to your newly created OAuth client
- This downloads a JSON file (e.g., `client_secret_xxxxx.json`)
- **This is the file users upload in Step 2 of the web interface**

---

## Step 2: Set BASE_URL Environment Variable

### For Railway:
1. Go to your Railway project dashboard
2. Click on your service
3. Go to "Variables" tab
4. Add new variable:
   - **Name**: `BASE_URL`
   - **Value**: `https://your-app-name.up.railway.app`
   - Replace with your actual Railway URL

### For Render:
1. Go to your Render dashboard
2. Select your service
3. Go to "Environment" section
4. Add environment variable:
   - **Key**: `BASE_URL`
   - **Value**: `https://your-app-name.onrender.com`

### For Fly.io:
```bash
fly secrets set BASE_URL=https://your-app-name.fly.dev
```

### For Google Cloud Run:
```bash
gcloud run services update your-service-name \
  --set-env-vars="BASE_URL=https://your-service-url.run.app"
```

### For Heroku:
```bash
heroku config:set BASE_URL=https://your-app-name.herokuapp.com
```

### For Self-Hosted (Docker):
```bash
docker run -d \
  -p 80:8000 \
  -e BASE_URL=https://yourdomain.com \
  -e APIFY_TOKEN=your_token \
  your-image-name
```

---

## Step 3: Update OAuth Redirect URI When URL Changes

⚠️ **Important**: If your production URL changes, you must update:

1. **Google Cloud Console**:
   - Go to "Credentials" → Edit your OAuth client
   - Update "Authorized redirect URIs"
   - Add new URL: `https://new-url.com/api/oauth-callback`

2. **Environment Variable**:
   - Update `BASE_URL` in your platform's settings

---

## Step 4: Test the OAuth Flow

1. Open your deployed app in a browser
2. Upload the OAuth credentials JSON file
3. Click "Connect to Google Sheets"
4. A popup should open with Google's consent screen
5. Grant permissions
6. Popup should close automatically with success message

---

## Troubleshooting

### "Popup blocked"
- Allow popups for your site
- Try again

### "redirect_uri_mismatch" error
- Check that `BASE_URL` environment variable matches your actual URL
- Verify the redirect URI in Google Cloud Console includes `/api/oauth-callback`
- Make sure there are no trailing slashes

### OAuth screen shows "This app isn't verified"
- This is normal for testing
- Click "Advanced" → "Go to [App Name] (unsafe)"
- For production use, submit your app for verification

### "Invalid OAuth state"
- Clear browser cache and cookies
- Re-upload credentials
- Try again

### Popup closes but no success message
- Check browser console for errors
- Verify BASE_URL is set correctly
- Check server logs for errors

---

## Security Notes

### For Production:

1. **Keep credentials file secure**: 
   - Don't commit to git
   - Don't share publicly
   - Rotate if compromised

2. **Use HTTPS**: 
   - Google OAuth requires HTTPS in production
   - All recommended platforms provide free SSL

3. **Set ALLOWED_ORIGINS**:
   - Don't use `*` in production
   - Set to your actual domain
   - Example: `ALLOWED_ORIGINS=https://your-app.railway.app`

4. **Limit OAuth scopes**:
   - Only request necessary permissions
   - Current scopes: spreadsheets + drive.readonly

5. **Verify OAuth consent screen**:
   - Use your organization's branding
   - Clearly describe what access is needed
   - Add privacy policy URL if public

---

## For Internal/Team Use

If this tool is only for your team:

1. **Keep app in "Testing" mode** in Google Cloud Console
2. **Add team members as test users**
3. **No need for app verification**
4. **Each team member downloads their own OAuth credentials**

---

## Environment Variables Summary

Required for OAuth to work:
```bash
BASE_URL=https://your-production-url.com
```

Full production setup:
```bash
# Required
APIFY_TOKEN=apify_api_xxxxx
BASE_URL=https://your-production-url.com

# Recommended
ALLOWED_ORIGINS=https://your-production-url.com
LOG_LEVEL=info
```

---

## Quick Reference

| Platform | BASE_URL Format |
|----------|----------------|
| Railway | `https://your-app-name.up.railway.app` |
| Render | `https://your-app-name.onrender.com` |
| Fly.io | `https://your-app-name.fly.dev` |
| Cloud Run | `https://your-service-xxxxx.run.app` |
| Heroku | `https://your-app-name.herokuapp.com` |
| Custom Domain | `https://yourdomain.com` |

---

## Next Steps

After setup:
1. ✅ Deploy your app
2. ✅ Set `BASE_URL` environment variable
3. ✅ Configure Google Cloud Console redirect URI
4. ✅ Download OAuth credentials
5. ✅ Test the OAuth flow
6. ✅ Share credentials with your team

---

**Need help?** Check the [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for platform-specific deployment instructions.

