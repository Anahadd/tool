# 🚀 Deployment Guide - Kalshi Impressions Tool

This guide provides comprehensive deployment options for the Kalshi Impressions Tool.

---

## ✅ Deployment Readiness Checklist

Your application is now **production-ready** with the following features:

- ✅ **Security**: Configurable CORS origins
- ✅ **Environment Configuration**: All settings via environment variables
- ✅ **Health Checks**: `/api/health` endpoint for monitoring
- ✅ **Production Logging**: Configurable log levels
- ✅ **Docker Support**: Optimized Dockerfile with Playwright support
- ✅ **Auto-scaling Ready**: Stateless design (config stored per-user)
- ✅ **Port Flexibility**: Reads `PORT` from environment

---

## 🎯 Recommended Deployment Options

### 1. Railway.app ⭐ (Recommended - Easiest)

**Best for**: Quick deployment, automatic scaling, built-in domains

**Steps**:
1. Push your code to GitHub
2. Go to [Railway.app](https://railway.app)
3. Click "New Project" → "Deploy from GitHub"
4. Select your repository
5. Add environment variables:
   - `APIFY_TOKEN` = your_apify_token (required)
   - `ALLOWED_ORIGINS` = https://your-app.railway.app (optional, for security)
   - `LOG_LEVEL` = info (optional)
6. Deploy!

**Cost**: ~$5-20/month depending on usage

**Domain**: `https://your-app-name.up.railway.app`

**Configuration**: Uses `railway.json` and `Dockerfile`

---

### 2. Render.com

**Best for**: Free tier, automatic SSL, easy setup

**Steps**:
1. Go to [Render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Environment**: Docker
   - **Region**: Choose closest to your users
   - **Instance Type**: Free or Starter ($7/month)
5. Add environment variables:
   - `APIFY_TOKEN` = your_apify_token
   - `ALLOWED_ORIGINS` = https://your-app.onrender.com
6. Deploy!

**Cost**: Free tier available, or $7/month for always-on

**Note**: Free tier sleeps after 15 mins of inactivity

---

### 3. Fly.io

**Best for**: Global edge deployment, low latency

**Steps**:
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Initialize and deploy
fly launch
```

**Configuration**: Create `fly.toml`:
```toml
app = "kalshi-impressions"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8000"

[[services]]
  http_checks = []
  internal_port = 8000
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80
    force_https = true

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [[services.http_checks]]
    interval = 10000
    grace_period = "5s"
    method = "get"
    path = "/api/health"
    protocol = "http"
    timeout = 2000
```

**Cost**: ~$3-10/month depending on usage

---

### 4. Google Cloud Run

**Best for**: Pay-per-use, scales to zero, Google Cloud integration

**Steps**:
```bash
# Install gcloud CLI
# Then authenticate
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Build and deploy
gcloud run deploy kalshi-impressions \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="APIFY_TOKEN=your_token"
```

**Cost**: Pay only when running (very economical for low traffic)

---

### 5. AWS (ECS/Elastic Beanstalk)

**Best for**: Enterprise deployments, full AWS integration

#### Option A: ECS (Elastic Container Service)

**Steps**:
1. Create ECR repository and push Docker image
2. Create ECS cluster
3. Create task definition using your Docker image
4. Create service with load balancer
5. Set environment variables in task definition

#### Option B: Elastic Beanstalk

**Steps**:
```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p docker kalshi-impressions

# Create environment
eb create kalshi-prod --envvars APIFY_TOKEN=your_token

# Deploy
eb deploy
```

**Cost**: ~$15-50/month depending on instance size

---

### 6. Azure Container Apps

**Best for**: Microsoft ecosystem, enterprise integration

**Steps**:
```bash
# Install Azure CLI
az login

# Create resource group
az group create --name kalshi-rg --location eastus

# Create container app
az containerapp create \
  --name kalshi-impressions \
  --resource-group kalshi-rg \
  --image DOCKER_HUB_IMAGE \
  --environment my-environment \
  --ingress external \
  --target-port 8000 \
  --env-vars APIFY_TOKEN=your_token
```

**Cost**: ~$5-20/month

---

### 7. DigitalOcean App Platform

**Best for**: Simple pricing, managed infrastructure

**Steps**:
1. Go to [DigitalOcean](https://cloud.digitalocean.com/apps)
2. Click "Create App"
3. Select your GitHub repository
4. Choose "Dockerfile" as build method
5. Add environment variables
6. Deploy!

**Cost**: $5-12/month for basic plan

---

### 8. Heroku

**Best for**: Traditional PaaS, easy deployment

**Steps**:
```bash
# Install Heroku CLI
# Login
heroku login

# Create app
heroku create kalshi-impressions

# Set environment variables
heroku config:set APIFY_TOKEN=your_token

# Deploy
git push heroku main
```

**Uses**: `Procfile` for deployment

**Cost**: ~$7/month (Eco dyno)

---

### 9. Self-Hosted (VPS)

**Best for**: Full control, custom infrastructure

**Providers**: Linode, Vultr, Hetzner, AWS EC2

**Steps**:
```bash
# SSH into your server
ssh user@your-server.com

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Clone repository
git clone https://github.com/yourusername/your-repo.git
cd your-repo

# Build Docker image
docker build -t kalshi-impressions .

# Run container
docker run -d \
  -p 80:8000 \
  -e APIFY_TOKEN=your_token \
  -e ALLOWED_ORIGINS=https://yourdomain.com \
  --name kalshi-impressions \
  --restart unless-stopped \
  kalshi-impressions
```

**Optional**: Set up Nginx reverse proxy + SSL with Let's Encrypt

**Cost**: $5-20/month for VPS

---

## 🔐 Environment Variables Reference

### Required

- `APIFY_TOKEN` - Your Apify API token for Instagram scraping
  - Get from: https://console.apify.com/account/integrations
  - Format: `apify_api_xxxxxxxxx`

### Optional (Security & Configuration)

- `ALLOWED_ORIGINS` - Comma-separated list of allowed CORS origins
  - Default: `*` (allow all - not recommended for production)
  - Example: `https://yourdomain.com,https://app.yourdomain.com`
  - Single origin: `https://yourdomain.com`

- `HOST` - Server bind address
  - Default: `0.0.0.0` (when PORT is set), `127.0.0.1` (local dev)
  - Usually don't need to change

- `PORT` - Server port
  - Default: `8000`
  - Most platforms set this automatically

- `LOG_LEVEL` - Logging verbosity
  - Options: `debug`, `info`, `warning`, `error`
  - Default: `info`

### Optional (Rate Limiting - Advanced)

See `env.example` for full list of rate limiting options:
- `TIKTOK_BATCH_SIZE` - URLs per TikTok batch (default: 20)
- `TIKTOK_BATCH_DELAY` - Seconds between batches (default: 1.0)
- `INSTAGRAM_BATCH_SIZE` - URLs per Instagram batch (default: 50)
- `INSTAGRAM_BATCH_DELAY` - Seconds between batches (default: 2.0)

---

## 🔍 Health Check Endpoint

All deployment platforms can use the health check endpoint:

**URL**: `/api/health`

**Response**:
```json
{
  "status": "healthy",
  "service": "kalshi-impressions-tool",
  "apify_configured": true
}
```

**Use for**:
- Load balancer health checks
- Monitoring systems
- Uptime checks

---

## 📊 Monitoring & Logging

### View Logs

**Railway**:
```bash
# View logs in dashboard or CLI
railway logs
```

**Render**:
- View in dashboard under "Logs" tab

**Fly.io**:
```bash
fly logs
```

**Docker (self-hosted)**:
```bash
docker logs kalshi-impressions
docker logs -f kalshi-impressions  # Follow logs
```

### Recommended Monitoring Services

- **Uptime Monitoring**: UptimeRobot, Pingdom, Better Uptime
- **Error Tracking**: Sentry, Rollbar
- **Performance**: New Relic, DataDog

---

## 🔒 Security Best Practices

1. **Set ALLOWED_ORIGINS**: Never use `*` in production
   ```bash
   ALLOWED_ORIGINS=https://yourdomain.com
   ```

2. **Use HTTPS**: All recommended platforms provide free SSL

3. **Secure API Tokens**: Never commit tokens to git
   - Use platform's secret management
   - Rotate tokens periodically

4. **Keep Dependencies Updated**:
   ```bash
   pip list --outdated
   pip install --upgrade -r requirements.txt
   ```

5. **Monitor Health**: Set up uptime monitoring

6. **Rate Limiting**: Configure batch sizes based on your usage

---

## 🎯 Quick Comparison

| Platform | Ease | Cost | Free Tier | SSL | Auto-scaling |
|----------|------|------|-----------|-----|--------------|
| Railway | ⭐⭐⭐⭐⭐ | $5-20 | Trial only | ✅ | ✅ |
| Render | ⭐⭐⭐⭐⭐ | $0-7 | ✅ | ✅ | ✅ |
| Fly.io | ⭐⭐⭐⭐ | $3-10 | Limited | ✅ | ✅ |
| Google Cloud Run | ⭐⭐⭐ | Pay-per-use | ✅ | ✅ | ✅ |
| Heroku | ⭐⭐⭐⭐ | $7+ | No | ✅ | ✅ |
| DigitalOcean | ⭐⭐⭐⭐ | $5-12 | Trial only | ✅ | ✅ |
| Self-hosted VPS | ⭐⭐ | $5-20 | No | Manual | No |

---

## 🚦 Testing Your Deployment

After deployment, verify everything works:

1. **Health Check**:
   ```bash
   curl https://your-app.com/api/health
   ```

2. **Frontend**: Open `https://your-app.com` in browser

3. **API Docs**: Visit `https://your-app.com/docs`

4. **Upload Flow**: Test the complete workflow:
   - Enter Apify token
   - Upload Google credentials
   - Connect to Google Sheets
   - Run an update

---

## 📝 Post-Deployment Checklist

- [ ] Health check endpoint responding
- [ ] Frontend loads correctly
- [ ] API documentation accessible at `/docs`
- [ ] Environment variables configured
- [ ] CORS origins set correctly
- [ ] Apify token working
- [ ] Google Sheets integration tested
- [ ] SSL certificate active (HTTPS)
- [ ] Monitoring/uptime checks configured
- [ ] Logs accessible

---

## 🐛 Troubleshooting

### Container fails to start
- Check logs for errors
- Verify `PORT` environment variable
- Ensure Playwright dependencies installed

### Health check fails
- Check if port is correct
- Verify application is running
- Check firewall rules

### Slow response times
- Reduce batch sizes in environment variables
- Increase instance size/RAM
- Check Apify quota

### Google Sheets authentication fails
- Ensure credentials file is uploaded
- Check OAuth scopes
- Verify spreadsheet permissions

---

## 📞 Support

For issues:
1. Check application logs
2. Verify environment variables
3. Review platform documentation
4. Check health endpoint

Built by anahad for Kalshi Internal

---

**Happy Deploying! 🚀**

