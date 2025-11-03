# Service Account Setup (Simple!)

##  Why Service Accounts?
- **No OAuth complexity** - no popups, no token expiration
- **No per-user credentials** - one account for the whole app
- **Just share and go** - users share their sheet with one email

## Setup (One Time - 5 minutes)

### 1. Create Service Account
1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts
2. Select your Google Cloud project
3. Click **"+ CREATE SERVICE ACCOUNT"**
4. Name: `impressions-tool-service`
5. Click **"CREATE AND CONTINUE"**
6. Skip roles - click **"CONTINUE"** then **"DONE"**

### 2. Create Key
1. Click on the service account you just created
2. Go to **"KEYS"** tab
3. Click **"ADD KEY"** → **"Create new key"**
4. Choose **"JSON"**
5. Click **"CREATE"**
6. Save the downloaded JSON file

### 3. Enable Google Sheets API
1. Go to https://console.cloud.google.com/apis/library
2. Search for "Google Sheets API"
3. Click **"ENABLE"**

### 4. Deploy to Railway
1. Upload the service account JSON to Railway
2. Set environment variable:
   ```
   GOOGLE_SHEETS_CREDS=/path/to/service-account.json
   ```

### 5. Get the Service Account Email
Open the JSON file and find the `client_email` field:
```json
{
  "client_email": "impressions-tool-service@your-project.iam.gserviceaccount.com"
}
```

## Usage (For End Users)

### Super Simple - 3 Steps:
1. Open your Google Sheet
2. Click **"Share"** (top right)
3. Add this email with **Editor** access:
   ```
   impressions-tool-service@your-project.iam.gserviceaccount.com
   ```

That's it! No credentials to upload, no OAuth popups, no expiration!

## What We Removed
- ❌ OAuth flow
- ❌ Credential uploads per user
- ❌ Token storage in Firestore
- ❌ Token refresh logic
- ❌ "Connect to Google Sheets" button complexity

## What Users Do Now
- ✅ Just share their sheet with one email
- ✅ No authentication needed
- ✅ Works forever (no expiration)

