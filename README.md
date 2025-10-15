# Kalshi Internal - Impressions Tool

Built by anahad

Fetch TikTok and Instagram stats and automatically update Google Sheets.

## 🚀 Quick Start

### Web Interface (Easiest)

The tool now has a web interface! Just run:

```bash
python3 web_app.py
```

Then open: http://127.0.0.1:8000

## 📦 Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for TikTok)
python -m playwright install chromium

# Run the web app
python3 web_app.py
```

## 🌐 Deployment

Your application is **production-ready**! Deploy to any of these platforms:

- **Railway.app** ⭐ (Recommended - Easiest)
- **Render.com** (Free tier available)
- **Fly.io** (Global edge deployment)
- **Google Cloud Run** (Pay-per-use)
- **Heroku, AWS, Azure, DigitalOcean** (Enterprise options)
- **Self-hosted VPS** (Full control)

**See [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) for detailed instructions** for each platform.

## 📚 Documentation

- **Web interface**: Open http://127.0.0.1:8000
- **API docs**: http://127.0.0.1:8000/docs
- **Deployment**: See `DEPLOYMENT_GUIDE.md`
- **OAuth Setup** (for production): See `OAUTH_SETUP.md`

## ✅ Features

- ✅ TikTok scraping (Playwright-based)
- ✅ Instagram scraping (Apify-based)
- ✅ Google Sheets integration
- ✅ Web interface with live updates
- ✅ Token persistence
- ✅ Deployment ready

Built by anahad for Kalshi Internal
