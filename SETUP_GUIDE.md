# 🚀 Complete Setup Guide - Kalshi Impressions Tool

## Prerequisites

- [ ] Google Cloud account
- [ ] Apify account (for Instagram scraping)
- [ ] Railway account (or other hosting platform)
- [ ] Google Sheet to update

---

## Part 1: Google Cloud Console Setup (OAuth)

### Step 1: Create/Select a Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top
3. Click **"New Project"**
   - Name: `Kalshi Impressions Tool`
   - Click **"Create"**
4. Wait for project creation, then select it

### Step 2: Enable Required APIs

1. In the left menu, click **"APIs & Services"** → **"Library"**
2. Search for and enable these APIs:
   - **Google Sheets API** - Click "Enable"
   - **Google Drive API** - Click "Enable"

### Step 3: Configure OAuth Consent Screen

1. Go to **"APIs & Services"** → **"OAuth consent screen"**
2. Choose **"External"** (unless you have Google Workspace)
3. Fill in the required fields:
   - **App name**: `Kalshi Impressions Tool`
   - **User support email**: Your email
   - **Developer contact**: Your email
4. Click **"Save and Continue"**
5. On the **"Scopes"** page:
   - Click **"Add or Remove Scopes"**
   - Manually add these scopes:
     - `https://www.googleapis.com/auth/spreadsheets`
     - `https://www.googleapis.com/auth/drive.readonly`
   - Click **"Update"**
   - Click **"Save and Continue"**
6. On the **"Test users"** page:
   - Click **"+ Add Users"**
   - Add your email and any team members' emails
   - Click **"Save and Continue"**
7. Click **"Back to Dashboard"**

### Step 4: Create OAuth 2.0 Credentials (IMPORTANT!)

⚠️ **Common Mistake**: Don't use "Desktop" application type!

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
3. **Application type**: Select **"Web application"** ✅ (NOT Desktop!)
4. **Name**: `Kalshi Impressions - Production`
5. **Authorized redirect URIs**:
   - Click **"+ ADD URI"**
   - If deploying to Railway, add:
     ```
     https://YOUR-APP-NAME.up.railway.app/api/oauth-callback
     ```
   - Replace `YOUR-APP-NAME` with your actual Railway subdomain
   - For local testing, also add:
     ```
     http://localhost:8000/api/oauth-callback
     ```
6. Click **"CREATE"**
7. **Download the credentials**:
   - In the popup, click **"DOWNLOAD JSON"**
   - Save this file as `credentials.json`
   - Keep it secure! Don't commit to git!

---

## Part 2: Get Your Apify Token

1. Go to [Apify Console](https://console.apify.com/account/integrations)
2. Sign up or log in
3. Copy your **API Token** (starts with `apify_api_`)
4. Save this for later

---

## Part 3: Deploy to Railway

### Step 1: Fork/Clone the Repository

```bash
# Clone the repository
git clone https://github.com/Anahadd/tool.git
cd tool

# Or fork it on GitHub and clone your fork
```

### Step 2: Deploy to Railway

1. Go to [Railway.app](https://railway.app)
2. Sign up or log in
3. Click **"New Project"** → **"Deploy from GitHub repo"**
4. Select the repository
5. Railway will start building

### Step 3: Configure Environment Variables

⚠️ **CRITICAL**: Set these environment variables in Railway!

1. In Railway, click on your service
2. Go to **"Variables"** tab
3. Add these variables:

**Required:**
```bash
APIFY_TOKEN=apify_api_xxxxxxxxxxxxx
BASE_URL=https://YOUR-APP-NAME.up.railway.app
```

**Recommended:**
```bash
ALLOWED_ORIGINS=https://YOUR-APP-NAME.up.railway.app
LOG_LEVEL=info
```

⚠️ **Important Notes**:
- **No trailing slash** on `BASE_URL`! 
  - ✅ Correct: `https://tool-production-2495.up.railway.app`
  - ❌ Wrong: `https://tool-production-2495.up.railway.app/`
- Replace `YOUR-APP-NAME` with your actual Railway subdomain
- Find your Railway URL in the **"Settings"** → **"Domains"** section

### Step 4: Find Your Railway URL

1. In Railway, click on your service
2. Go to **"Settings"** → **"Domains"**
3. You'll see a URL like: `https://tool-production-xxxx.up.railway.app`
4. Copy this exact URL
5. Use it for `BASE_URL` (without trailing slash)

---

## Part 4: Update Google Cloud Console with Railway URL

⚠️ **CRITICAL**: You must update the redirect URI with your actual Railway URL!

1. Go back to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **"APIs & Services"** → **"Credentials"**
3. Click on your **"Web application"** OAuth client
4. Under **"Authorized redirect URIs"**:
   - If you added a placeholder earlier, **delete it**
   - Click **"+ ADD URI"**
   - Add your actual Railway URL + `/api/oauth-callback`:
     ```
     https://YOUR-ACTUAL-RAILWAY-URL.up.railway.app/api/oauth-callback
     ```
   - Example: `https://tool-production-2495.up.railway.app/api/oauth-callback`
5. Click **"SAVE"**
6. Wait 1-2 minutes for changes to take effect

---

## Part 5: Test the Application

### Step 1: Open Your Deployed App

1. Go to your Railway URL: `https://your-app.up.railway.app`
2. You should see the **"Kalshi Internal - Impressions Tool"** interface

### Step 2: Upload OAuth Credentials

1. In **Step 1: Google Credentials**:
   - Click or drag-and-drop your `credentials.json` file
   - Make sure it's the **Web application** credentials (not Desktop!)
   - You should see a green checkmark

### Step 3: Connect to Google Sheets

1. Click **"Connect to Google Sheets"** button
2. A popup window should open with Google's consent screen
3. **If you see an error**:
   - Check that `BASE_URL` is set correctly in Railway
   - Check that redirect URI in Google Cloud Console matches exactly
   - Try in an incognito window
4. Sign in with your Google account
5. Grant the requested permissions
6. Popup should close automatically with success message

### Step 4: Configure Sheet

1. In **Step 2: Sheet Configuration**:
   - Enter your Google Sheet URL
   - Enter the worksheet/tab name (e.g., "Sheet1")
   - Click **"Save as Defaults"** (optional)

### Step 5: Run Update

1. Click **"🚀 RUN UPDATE"** button
2. Wait for the process to complete
3. Check your Google Sheet - data should be updated!

---

## 🐛 Common Issues & Solutions

### Issue 1: "redirect_uri_mismatch" Error

**Symptoms**: Can't complete OAuth, Google shows error 400

**Solutions**:
1. Check `BASE_URL` in Railway has **no trailing slash**
2. Check redirect URI in Google Cloud Console matches exactly:
   ```
   https://your-app.railway.app/api/oauth-callback
   ```
3. Make sure you're using **Web application** credentials (not Desktop)
4. Wait 1-2 minutes after changing Google Cloud settings

### Issue 2: "This app isn't verified" Warning

**Symptoms**: Google shows warning during OAuth

**Solution**: This is normal for testing!
- Click **"Advanced"**
- Click **"Go to Kalshi Impressions Tool (unsafe)"**
- This only appears for test users
- To remove: Submit app for verification (not required for internal use)

### Issue 3: Upload Credentials Works, But Connect Fails

**Symptoms**: Credentials upload succeeds, but OAuth fails

**Solutions**:
1. Make sure you downloaded **Web application** credentials
2. Check if you accidentally used Desktop credentials:
   - Open `credentials.json` in text editor
   - Should have `"web": {` not `"installed": {`
3. If wrong type, delete and create new **Web application** credentials

### Issue 4: "Google Sheets not connected" After OAuth

**Symptoms**: OAuth succeeds but update fails

**Solutions**:
1. Make sure you completed OAuth flow in the popup
2. Hard refresh the page (`Ctrl/Cmd + Shift + R`)
3. Try uploading credentials and connecting again
4. Check Railway logs for specific errors

### Issue 5: Popup Blocked

**Symptoms**: OAuth popup doesn't open

**Solutions**:
1. Allow popups for your Railway site
2. Try clicking the button again
3. Check browser console for errors

---

## 📋 Quick Checklist

Use this checklist when setting up:

### Google Cloud Console:
- [ ] Project created
- [ ] Google Sheets API enabled
- [ ] Google Drive API enabled
- [ ] OAuth consent screen configured
- [ ] Test users added
- [ ] **Web application** OAuth client created (NOT Desktop)
- [ ] Redirect URI added: `https://your-app.railway.app/api/oauth-callback`
- [ ] Credentials JSON downloaded

### Railway:
- [ ] Repository deployed
- [ ] `APIFY_TOKEN` environment variable set
- [ ] `BASE_URL` environment variable set (no trailing slash!)
- [ ] `ALLOWED_ORIGINS` environment variable set (optional)
- [ ] Deployment successful
- [ ] Railway URL copied

### Google Cloud Console (Again):
- [ ] Redirect URI updated with actual Railway URL
- [ ] Clicked "SAVE"
- [ ] Waited 1-2 minutes

### Testing:
- [ ] App loads in browser
- [ ] Credentials upload works
- [ ] OAuth popup opens
- [ ] OAuth completes successfully
- [ ] Sheet configuration saved
- [ ] Run update works
- [ ] Data appears in Google Sheet

---

## 🔐 Security Best Practices

1. **Never commit credentials**:
   - `credentials.json` should be in `.gitignore`
   - Upload it manually through the web interface

2. **Use specific CORS origins in production**:
   ```bash
   ALLOWED_ORIGINS=https://your-actual-domain.com
   ```

3. **Limit OAuth scopes**:
   - Only request spreadsheets and drive.readonly
   - Never request more permissions than needed

4. **Keep test users list minimal**:
   - Only add people who need access
   - Remove users when they leave

5. **Rotate tokens periodically**:
   - Regenerate Apify token every 6 months
   - Create new OAuth credentials if compromised

---

## 📞 Need Help?

If you encounter issues:

1. **Check the logs**:
   - Railway: Deployments tab → Click deployment → View logs
   - Look for DEBUG lines showing what went wrong

2. **Common log messages**:
   - `redirect_uri_mismatch` → Check BASE_URL and Google Cloud URI
   - `missing fields refresh_token` → Use Web credentials, not Desktop
   - `Google Sheets not connected` → Complete OAuth flow

3. **Verify your setup**:
   - Use the checklist above
   - Double-check every step
   - Pay special attention to URLs (no typos!)

---

## 🎉 You're Done!

Your Kalshi Impressions Tool is now deployed and ready to use!

**What you can do**:
- Update TikTok and Instagram stats automatically
- Integrate with Google Sheets
- Share the deployed app with your team
- Run updates on demand

**Next steps**:
- Add more team members as test users
- Set up regular update schedules
- Monitor usage in Railway dashboard

Built by anahad for Kalshi Internal

