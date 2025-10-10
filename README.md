# Impressions Tool

Fetch TikTok and Instagram stats and automatically update Google Sheets.

## Prerequisites

1. **Python 3.9 or higher**
   ```bash
   python3 --version
   ```
   If Python is not installed, download from [python.org](https://www.python.org/downloads/)

2. **Apify API Token** (for Instagram)
   - Sign up at [apify.com](https://apify.com)
   - Get your API token from [console.apify.com/account/integrations](https://console.apify.com/account/integrations)

3. **Google Cloud OAuth Credentials** (for Sheets)
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Sheets API
   - Create OAuth client credentials (Desktop App type)
   - Download the JSON file

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/Tool.git
cd Tool

# Install the tool
pip install .

# Or for development (editable install)
pip install -e .
```

**Note:** If you don't have pip installed, run:
```bash
python3 -m ensurepip --upgrade
```

## Setup

### 1. Set Your API Token

Set your Apify token as an environment variable:

```bash
export APIFY_TOKEN="your_apify_token_here"
```

**Note:** You'll need to run this export command in each new terminal session, or add it to your `~/.zshrc` or `~/.bashrc` to make it permanent:

```bash
echo 'export APIFY_TOKEN="your_apify_token_here"' >> ~/.zshrc
source ~/.zshrc
```

### 2. Connect Google Sheets

```bash
# Connect with OAuth (opens browser for authentication)
impressions connect-sheets --client-secrets ~/Downloads/client_secret.json

# Set your default spreadsheet and worksheet
impressions set-defaults "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit" "Sheet1"
```

This will save your credentials to `~/.tool_google/token.json` for future use.

## Usage

Update your Google Sheet with the latest stats:

```bash
impressions update-sheets
```

The tool will:
- Read URLs from your Google Sheet
- Fetch stats from TikTok and Instagram
- Update the sheet with views, likes, and comments

### Override Defaults

```bash
impressions update-sheets --spreadsheet "YOUR_SHEET_URL" --worksheet "Sheet1"
```

## Configuration Options

Optional environment variables in `.env`:

```bash
# Rate limiting (adjust if hitting API limits)
TIKTOK_BATCH_SIZE=20           # URLs per batch (default: 20)
INSTAGRAM_BATCH_SIZE=50        # URLs per batch (default: 50)
TIKTOK_BATCH_DELAY=1.0         # Seconds between batches (default: 1.0)
INSTAGRAM_BATCH_DELAY=2.0      # Seconds between batches (default: 2.0)

# Advanced options
ms_token=your_tiktok_token     # Optional: TikTok ms_token for better reliability
TIKTOK_BROWSER=chromium        # Browser: chromium/firefox/webkit
```

**Hitting rate limits?** Reduce batch sizes and increase delays:
```bash
export TIKTOK_BATCH_SIZE=10
export INSTAGRAM_BATCH_SIZE=25
export TIKTOK_BATCH_DELAY=2.0
export INSTAGRAM_BATCH_DELAY=3.0
```

## Security

⚠️ **Important:** Never commit sensitive files to Git:
- `*.json` (Google credentials) - already in `.gitignore`
- Never hardcode your API tokens in the code

**Always use environment variables** for API tokens and credentials.

## Troubleshooting

**Import errors?** Make sure all dependencies are installed:
```bash
pip install --upgrade --force-reinstall .
```

**Rate limit errors?** Reduce batch sizes (see Configuration Options above)

**Authentication errors?** Re-run the connect-sheets command:
```bash
impressions connect-sheets --client-secrets ~/Downloads/client_secret.json
```

## Updating

```bash
cd Tool
git pull origin main
pip install --upgrade --force-reinstall .
```

For editable installs, just run `git pull` - changes take effect immediately!

## License

MIT License - feel free to use and modify.
