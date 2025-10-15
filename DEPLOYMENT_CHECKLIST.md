# 📋 Deployment Checklist

Quick reference for deploying the Kalshi Impressions Tool.

## ✅ Pre-Deployment Verification

- [x] **Security**: CORS origins configurable via `ALLOWED_ORIGINS` env var
- [x] **Environment Config**: All settings read from environment variables
- [x] **Health Endpoint**: `/api/health` implemented and working
- [x] **Docker Optimized**: `.dockerignore` created, Dockerfile includes all dependencies
- [x] **Production Logging**: Configurable via `LOG_LEVEL` env var
- [x] **Port Binding**: Reads from `PORT` env var (required by most platforms)
- [x] **Static Files**: Properly served from `/static` directory
- [x] **Dependencies**: Listed in `requirements.txt` and `pyproject.toml`

## 🚀 Quick Start - Railway (Recommended)

1. **Prerequisites**:
   - [ ] GitHub repository created
   - [ ] Code pushed to GitHub
   - [ ] Apify token obtained from https://console.apify.com/account/integrations

2. **Deploy**:
   - [ ] Go to https://railway.app
   - [ ] Connect GitHub repository
   - [ ] Add environment variable: `APIFY_TOKEN=your_token`
   - [ ] (Optional) Add: `ALLOWED_ORIGINS=https://your-app.railway.app`
   - [ ] Deploy!

3. **Test**:
   - [ ] Visit `https://your-app.railway.app/api/health`
   - [ ] Open frontend at `https://your-app.railway.app`
   - [ ] Test full workflow (upload credentials, update sheets)

## 🔐 Required Environment Variables

### Minimal (Required)
```bash
APIFY_TOKEN=apify_api_xxxxxxxxxxxx
```

### Recommended (Production)
```bash
APIFY_TOKEN=apify_api_xxxxxxxxxxxx
ALLOWED_ORIGINS=https://your-domain.com
LOG_LEVEL=info
```

## 📝 Platform-Specific Notes

### Railway
- Uses `Dockerfile` automatically
- Health check configured in `railway.json`
- PORT is set automatically

### Render
- Choose "Docker" as environment
- Free tier available (sleeps after 15 mins)
- SSL included

### Fly.io
- Run `fly launch` to get started
- Create `fly.toml` (see DEPLOYMENT_GUIDE.md)
- Global edge network

### Google Cloud Run
- Fully managed, scales to zero
- Pay only for actual usage
- Use `gcloud run deploy` command

### Heroku
- Uses `Procfile` automatically
- Run `heroku config:set APIFY_TOKEN=xxx`
- Simple git-based deployment

### Self-Hosted
- Build with `docker build -t kalshi-impressions .`
- Run with `docker run -d -p 80:8000 -e APIFY_TOKEN=xxx kalshi-impressions`
- Configure reverse proxy + SSL

## 🔍 Post-Deployment Testing

```bash
# 1. Health check
curl https://your-app.com/api/health

# Should return:
# {
#   "status": "healthy",
#   "service": "kalshi-impressions-tool",
#   "apify_configured": true
# }

# 2. Frontend
# Open in browser: https://your-app.com

# 3. API Docs
# Open in browser: https://your-app.com/docs
```

## 🎯 Complete Workflow Test

1. [ ] Open app URL in browser
2. [ ] Enter Apify token and save
3. [ ] Upload Google OAuth credentials JSON
4. [ ] Click "Connect to Google Sheets"
5. [ ] Complete OAuth flow
6. [ ] Enter spreadsheet URL and worksheet name
7. [ ] Click "Run Update"
8. [ ] Verify data appears in Google Sheet

## 🐛 Common Issues

### "apify_configured": false
- Check APIFY_TOKEN environment variable is set
- Verify token format starts with `apify_api_`

### CORS errors in browser
- Set `ALLOWED_ORIGINS` to your domain
- Format: `https://your-domain.com` (no trailing slash)

### Container fails to start
- Check logs for Playwright installation errors
- Verify all dependencies in requirements.txt

### Port binding errors
- Ensure `PORT` env var is set (or defaults to 8000)
- Check no conflicting services on same port

## 📊 Monitoring Setup

1. **Uptime Monitoring**:
   - Use UptimeRobot, Pingdom, or Better Uptime
   - Monitor: `https://your-app.com/api/health`
   - Check interval: 5 minutes

2. **Error Tracking** (Optional):
   - Integrate Sentry for error tracking
   - Add DataDog for performance monitoring

3. **Log Aggregation**:
   - Most platforms have built-in log viewers
   - Check regularly for errors or warnings

## 🔒 Security Best Practices

- [ ] Set `ALLOWED_ORIGINS` (don't use `*` in production)
- [ ] Use HTTPS (provided by all recommended platforms)
- [ ] Never commit `.env` file or credentials to git
- [ ] Rotate API tokens periodically
- [ ] Monitor for suspicious activity
- [ ] Keep dependencies updated

## 📚 Additional Resources

- **Full Guide**: See `DEPLOYMENT_GUIDE.md` for detailed platform instructions
- **Configuration**: See `env.example` for all environment variables
- **API Docs**: Available at `/docs` endpoint on your deployment
- **Simple Deployment**: See `DEPLOY.md` for quick Railway setup

---

**Need Help?** Check the DEPLOYMENT_GUIDE.md for comprehensive troubleshooting and platform-specific instructions.

Built by anahad for Kalshi Internal

