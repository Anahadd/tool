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

## 🌐 Deploy to Railway

1. Push to GitHub
2. Go to https://railway.app
3. Deploy from GitHub repo
4. Add environment variable: `APIFY_TOKEN`
5. Done!

See `DEPLOY.md` for details.

## 📚 Documentation

- Web interface: Open http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- Deployment: See `DEPLOY.md`

## ✅ Features

- ✅ TikTok scraping (Playwright-based)
- ✅ Instagram scraping (Apify-based)
- ✅ Google Sheets integration
- ✅ Web interface with live updates
- ✅ Token persistence
- ✅ Deployment ready

Built by anahad for Kalshi Internal
