import asyncio
import os
from urllib.parse import urlparse
import re
import sys
import time
import main as tiktokmod
import ig as igmod
from apify_client import ApifyClient
from TikTokApi import TikTokApi
import gspread
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


CONFIG_DIR = Path(os.getenv("TOOL_CONFIG_DIR", str(Path.home() / ".tool_google")))
try:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass
CONFIG_FILE = CONFIG_DIR / "config.json"

# Optional service account JSON path (preferred for automation). If absent, we'll
# try OAuth user auth using a saved token created by the CLI.
SHEETS_CREDS = os.getenv("GOOGLE_SHEETS_CREDS", "")

# Spreadsheet URL or ID (URL recommended) - defaults to empty, use set-defaults or pass via CLI
SHEETS_SPREADSHEET = os.getenv("GOOGLE_SHEETS_SPREADSHEET", "")

# Worksheet/tab name - defaults to "Sheet1"
SHEETS_WORKSHEET = os.getenv("GOOGLE_SHEETS_WORKSHEET", "Sheet1")

# Only set to True if you want to open by title (requires Drive API)
SHEETS_ALLOW_TITLE = bool(os.getenv("GOOGLE_SHEETS_ALLOW_TITLE", ""))

OAUTH_CLIENT_FILE = Path(os.getenv("GOOGLE_OAUTH_CLIENT", str(CONFIG_DIR / "oauth_client.json")))
OAUTH_TOKEN_FILE = Path(os.getenv("GOOGLE_OAUTH_TOKEN", str(CONFIG_DIR / "token.json")))

# Batch size for processing URLs (to avoid rate limits and timeouts)
TIKTOK_BATCH_SIZE = int(os.getenv("TIKTOK_BATCH_SIZE", "20"))
INSTAGRAM_BATCH_SIZE = int(os.getenv("INSTAGRAM_BATCH_SIZE", "50"))

# Delay between batches in seconds (to manage rate limits)
TIKTOK_BATCH_DELAY = float(os.getenv("TIKTOK_BATCH_DELAY", "1.0"))
INSTAGRAM_BATCH_DELAY = float(os.getenv("INSTAGRAM_BATCH_DELAY", "2.0"))

def _log(msg: str, file=sys.stderr):
    """Print progress/status messages to stderr so stdout can be piped."""
    print(msg, file=file, flush=True)

def _progress(current: int, total: int, prefix: str = "Progress"):
    """Simple progress indicator."""
    if total > 0:
        pct = (current / total) * 100
        _log(f"{prefix}: {current}/{total} ({pct:.1f}%)")

def classify_urls(all_urls):
    tiktok_urls = tiktokmod.tiktok_video_links(all_urls)

    instagram_urls, seen = [], set()
    for u in all_urls:
        host = (urlparse(u).netloc or "").lower()
        if "instagram.com" in host:
            cu = igmod.canonicalize_instagram_url(u)
            if cu and cu not in seen:
                instagram_urls.append(cu)
                seen.add(cu)

    
    return tiktok_urls, instagram_urls


async def run_tiktok(urls, show_progress=False):
    """Fetch TikTok stats with batch processing and error handling."""
    if not urls:
        return []
    
    all_results = []
    total = len(urls)
    
    try:
        async with TikTokApi() as api:
            await api.create_sessions(
                ms_tokens=[tiktokmod.MS_TOKEN] if tiktokmod.MS_TOKEN else None,
                num_sessions=1,
                sleep_after=1,
                headless=True,
                browser=os.getenv("TIKTOK_BROWSER", "chromium"),
                # Increase timeout for slower environments (Railway, etc.)
                timeout=int(os.getenv("PLAYWRIGHT_TIMEOUT", "60000")),  # 60 seconds default
            )
            
            # Process in batches to avoid overwhelming the API
            for i in range(0, total, TIKTOK_BATCH_SIZE):
                batch = urls[i:i + TIKTOK_BATCH_SIZE]
                if show_progress:
                    _progress(i, total, "Fetching TikTok")
                
                try:
                    batch_results = await asyncio.gather(
                        *(tiktokmod.fetch_stats(api, u) for u in batch),
                        return_exceptions=True
                    )
                    # Handle individual failures
                    for idx, result in enumerate(batch_results):
                        if isinstance(result, Exception):
                            url = batch[idx]
                            _log(f"Warning: TikTok fetch failed for {url}: {result}")
                            all_results.append((url, "", "", "", "", f"error:{type(result).__name__}"))
                        else:
                            all_results.append(result)
                except Exception as e:
                    _log(f"Error processing TikTok batch {i//TIKTOK_BATCH_SIZE + 1}: {e}")
                    # Add error results for all URLs in failed batch
                    for url in batch:
                        all_results.append((url, "", "", "", "", f"batch_error:{type(e).__name__}"))
                
                # Configurable delay between batches to manage rate limits
                if i + TIKTOK_BATCH_SIZE < total:
                    await asyncio.sleep(TIKTOK_BATCH_DELAY)
            
            if show_progress:
                _progress(total, total, "Fetching TikTok")
    except Exception as e:
        _log(f"Fatal error initializing TikTok API: {e}")
        # Return error results for all URLs
        return [(url, "", "", "", "", f"fatal:{type(e).__name__}") for url in urls]
    
    return all_results


def run_instagram(urls, show_progress=False):
    """Fetch Instagram stats with error handling and validation."""
    if not urls:
        return []
    
    if not igmod.API_TOKEN or not igmod.API_TOKEN.startswith("apify_api_"):
        _log("Warning: APIFY_TOKEN not set or invalid. Instagram scraping may fail.")
        _log("Get your token at https://console.apify.com/account/integrations")
    
    try:
        client = ApifyClient(igmod.API_TOKEN)
        
        # Process in batches if there are many URLs
        all_items = []
        total = len(urls)
        
        for i in range(0, total, INSTAGRAM_BATCH_SIZE):
            batch = urls[i:i + INSTAGRAM_BATCH_SIZE]
            if show_progress:
                _progress(i, total, "Fetching Instagram")
            
            run_input = {
                "directUrls": batch,
                "resultsType": "posts",
                "resultsLimit": 1,
                "addParentData": False,
            }
            
            try:
                run = client.actor(igmod.ACTOR_ID).call(run_input=run_input)
                items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
                all_items.extend(items)
            except Exception as e:
                _log(f"Error processing Instagram batch {i//INSTAGRAM_BATCH_SIZE + 1}: {e}")
                # Continue with other batches rather than failing completely
                continue
            
            # Configurable delay between batches to manage rate limits
            if i + INSTAGRAM_BATCH_SIZE < total:
                time.sleep(INSTAGRAM_BATCH_DELAY)
        
        if show_progress:
            _progress(total, total, "Fetching Instagram")
        
        return all_items
    except Exception as e:
        _log(f"Fatal error with Instagram API: {e}")
        return []


# Note: url.txt functionality removed - use Google Sheets workflow only
# All URLs should be managed in Google Sheets via: impressions update-sheets


 

# =========================
# Google Sheets Integration
# =========================

def _col_index(headers: List[str], name_candidates: List[str]) -> int:
    names = [h.strip().lower() for h in headers]
    for cand in name_candidates:
        cand_l = cand.strip().lower()
        if cand_l in names:
            return names.index(cand_l) + 1  # 1-based for Sheets
    return 0

def _col_letter(col_index: int) -> str:
    s = ""
    n = col_index
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s

def _to_int(value: str) -> int:
    s = (value or "").strip()
    if not s:
        return 0
    try:
        return int(float(s.replace(",", "")))
    except Exception:
        return 0

def _extract_account_name(url: str) -> str:
    """Extract account/username from TikTok or Instagram URL."""
    if not url:
        return ""
    
    try:
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        parts = path.split('/')
        
        # TikTok URLs: tiktok.com/@username/video/...
        if "tiktok.com" in parsed.netloc.lower():
            for part in parts:
                if part.startswith('@'):
                    return part[1:]  # Remove @ symbol
        
        # Instagram URLs: instagram.com/username/p/... or instagram.com/reel/...
        elif "instagram.com" in parsed.netloc.lower():
            # Skip common paths that aren't usernames
            skip_paths = {'p', 'reel', 'reels', 'tv', 'stories'}
            if parts and parts[0] and parts[0] not in skip_paths:
                return parts[0]
            # If first part is 'p' or 'reel', there's no username in URL
            return ""
        
        return ""
    except Exception:
        return ""

def _extract_channel(url: str) -> str:
    """Extract platform/channel (TikTok or IG) from URL."""
    if not url:
        return ""
    
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        
        if "tiktok.com" in netloc:
            return "TikTok"
        elif "instagram.com" in netloc:
            return "IG"
        
        return ""
    except Exception:
        return ""

def _load_config_defaults() -> Dict[str, str]:
    try:
        import json
        if CONFIG_FILE.exists():
            data = json.loads(CONFIG_FILE.read_text())
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}
    return {}

def _save_config_defaults(spreadsheet: str, worksheet: str) -> None:
    try:
        import json
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps({
            "spreadsheet": spreadsheet,
            "worksheet": worksheet,
        }))
    except Exception:
        pass

def _open_sheet(
    creds_path: str,
    spreadsheet_title: str,
    worksheet_name: str = "Impressions",
    oauth_creds = None,
):
    val = (spreadsheet_title or "").strip()
    is_url = val.startswith("http://") or val.startswith("https://")
    is_key = bool(re.fullmatch(r"[-\w]{25,}", val))
    allow_title = bool(SHEETS_ALLOW_TITLE)

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    if not (is_url or is_key) and allow_title:
        scopes.append("https://www.googleapis.com/auth/drive.readonly")

    client = _authorize_gspread(scopes=scopes, service_account_path=creds_path, oauth_creds=oauth_creds)

    ss = None
    try:
        if is_url:
            ss = client.open_by_url(val)
        elif is_key:
            ss = client.open_by_key(val)
        elif allow_title:
            # Requires Drive API enabled on the project and drive.readonly scope
            ss = client.open(spreadsheet_title)
    except Exception:
        ss = None

    if ss is None:
        # Provide actionable guidance instead of triggering insufficient scopes
        if not (is_url or is_key) and not allow_title:
            raise RuntimeError(
                "Provide SHEETS_SPREADSHEET as a URL or ID in integrations.py, or set "
                "SHEETS_ALLOW_TITLE=True and enable the Google Drive API on the project."
            )
        raise RuntimeError("Failed to open Google Sheet; check URL/ID/title and credentials.")
    try:
        ws = ss.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        ws = ss.get_worksheet(0)
    return ws

def _authorize_gspread(scopes: List[str], service_account_path: str = "", oauth_creds = None):
    sa_path = (service_account_path or os.getenv("GOOGLE_SHEETS_CREDS") or "").strip()
    if sa_path:
        try:
            creds = ServiceAccountCredentials.from_service_account_file(sa_path, scopes=scopes)
            return gspread.authorize(creds)
        except Exception:
            # fall through to OAuth
            pass

    # Check for OAuth credentials passed from web app (in-memory)
    creds = None
    if oauth_creds:
        # Use the Credentials object directly - no JSON serialization needed!
        creds = oauth_creds
        _log("Using OAuth credentials from web app memory")
    
    # Fall back to OAuth token from file (for CLI usage)
    if not creds and OAUTH_TOKEN_FILE.exists():
        try:
            creds = UserCredentials.from_authorized_user_file(str(OAUTH_TOKEN_FILE), scopes)
        except Exception:
            creds = None
    
    # Refresh if expired
    if creds and getattr(creds, "expired", False) and getattr(creds, "refresh_token", None):
        try:
            creds.refresh(Request())
            _log("Refreshed expired OAuth token")
        except Exception as e:
            _log(f"Failed to refresh token: {e}")
            creds = None
            try:
                if OAUTH_TOKEN_FILE.exists():
                    OAUTH_TOKEN_FILE.unlink()
            except Exception:
                pass
    
    if not creds:
        raise RuntimeError(
            "Google Sheets not connected. Run `impressions connect-sheets` to link your "
            "Google account, or provide GOOGLE_SHEETS_CREDS path to a service account JSON "
            "and share your Sheet with that service account."
        )
    return gspread.authorize(creds)

def connect_sheets_oauth(scopes: List[str] = None, client_secrets_path: str = "") -> str:
    use_scopes = scopes or [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    client_file = Path(client_secrets_path) if client_secrets_path else OAUTH_CLIENT_FILE
    if not client_file.exists():
        raise RuntimeError(
            f"OAuth client secrets not found at {client_file}. Download a Desktop App OAuth JSON "
            f"from Google Cloud Console and save it there, or pass --client-secrets."
        )
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    flow = InstalledAppFlow.from_client_secrets_file(str(client_file), use_scopes)
    creds = flow.run_local_server(port=0)
    OAUTH_TOKEN_FILE.write_text(creds.to_json())
    return str(OAUTH_TOKEN_FILE)

async def update_sheet_views_likes_comments(
    spreadsheet: Optional[str] = None,
    worksheet: Optional[str] = None,
    creds_path: Optional[str] = None,
    disabled_columns: Optional[List[str]] = None,
    override: bool = True,
    start_row: Optional[int] = None,
    end_row: Optional[int] = None,
    oauth_creds = None,
):
    """Update Google Sheet with latest stats. Production-ready with error handling and progress tracking."""
    try:
        cfg = _load_config_defaults()
        spreadsheet_title = (spreadsheet or os.getenv("GOOGLE_SHEETS_SPREADSHEET") or cfg.get("spreadsheet") or SHEETS_SPREADSHEET)
        worksheet_name = (worksheet or os.getenv("GOOGLE_SHEETS_WORKSHEET") or cfg.get("worksheet") or SHEETS_WORKSHEET)
        creds_path = (creds_path or os.getenv("GOOGLE_SHEETS_CREDS") or SHEETS_CREDS)

        if not spreadsheet_title:
            raise ValueError(
                "No spreadsheet specified. Run `impressions set-defaults GOOGLE_SHEET_URL_LINK SHEET_NAME` first, "
                "or pass --spreadsheet flag."
            )

        _log(f"Opening spreadsheet: {spreadsheet_title[:50]}...")
        ws = _open_sheet(creds_path, spreadsheet_title, worksheet_name, oauth_creds=oauth_creds)
        
        _log("Reading sheet data...")
        values = ws.get_all_values()
        if not values:
            _log("Warning: Sheet is empty")
            return
        
        headers = values[0]
        url_col = _col_index(headers, ["url", "link"])
        name_col = _col_index(headers, ["name", "username", "account", "account name"])
        channel_col = _col_index(headers, ["channel", "platform", "source"])
        views_col = _col_index(headers, ["views", "plays"])
        likes_col = _col_index(headers, ["likes", "hearts"])
        comments_col = _col_index(headers, ["comments", "comment_count"])
        impressions_col = _col_index(headers, ["impressions"])
        last_changed_col = _col_index(headers, ["last changed", "last_changed", "last updated", "updated"])
        date_col = _col_index(headers, ["date", "date added", "date_added", "run date", "run_date"])
        
        # Only URL column is required
        if url_col == 0:
            raise ValueError("Missing required URL column. Please add a 'URL' or 'Link' column to your sheet.")
        
        # Process disabled columns
        disabled_cols_set = set(disabled_columns or [])
        
        # Helper function to check if a column should be updated
        def _is_col_enabled(col_name: str) -> bool:
            return col_name.lower() not in disabled_cols_set
        
        # Disable columns based on user input
        if not _is_col_enabled("name"):
            name_col = 0
        if not _is_col_enabled("channel"):
            channel_col = 0
        if not _is_col_enabled("views"):
            views_col = 0
        if not _is_col_enabled("likes"):
            likes_col = 0
        if not _is_col_enabled("comments"):
            comments_col = 0
        if not _is_col_enabled("impressions"):
            impressions_col = 0
        if not _is_col_enabled("last changed") and not _is_col_enabled("last_changed"):
            last_changed_col = 0
        if not _is_col_enabled("date"):
            date_col = 0
        
        # Log which optional columns are present and will be updated
        present_cols = []
        if name_col: present_cols.append("name")
        if channel_col: present_cols.append("channel")
        if views_col: present_cols.append("views")
        if likes_col: present_cols.append("likes")
        if comments_col: present_cols.append("comments")
        if impressions_col: present_cols.append("impressions")
        if last_changed_col: present_cols.append("last changed")
        if date_col: present_cols.append("date")
        _log(f"Found columns: URL + {', '.join(present_cols) if present_cols else 'no optional columns'}")
        
        # Log disabled columns if any
        if disabled_cols_set:
            _log(f"Disabled columns: {', '.join(sorted(disabled_cols_set))}")
        
        # Log override mode
        if not override:
            _log("Override mode: FALSE - will only fill empty cells")
        else:
            _log("Override mode: TRUE - will overwrite existing data")

        # Determine row range to process
        process_start_idx = 1  # Start from row 2 (index 1), skip header
        process_end_idx = len(values)  # Process all rows by default
        
        if start_row is not None:
            process_start_idx = max(1, start_row - 1)  # Convert to 0-based index
            if process_start_idx >= len(values):
                _log(f"Start row {start_row} is beyond the last row in the sheet ({len(values)})")
                return
        
        if end_row is not None:
            process_end_idx = min(len(values), end_row)
            if end_row >= len(values):
                _log(f"End row {end_row} is beyond the last row in the sheet ({len(values)}), processing until end")
        
        if start_row or end_row:
            actual_start = process_start_idx + 1
            actual_end = process_end_idx
            _log(f"Processing rows {actual_start} to {actual_end} (out of {len(values)} total rows)")
        
        # Gather rows and classify URLs (use already-fetched values)
        row_to_url: Dict[int, str] = {}
        tiktok_rows: List[int] = []
        instagram_rows: List[int] = []
        raw_urls: List[str] = []

        for i in range(process_start_idx, process_end_idx):  # Skip header row (index 0) and respect row range
            r = i + 1  # Convert to 1-based row number
            url_val = values[i][url_col - 1] if url_col <= len(values[i]) else ""
            # Clean URL (remove @ prefix and whitespace)
            u = tiktokmod.clean_url(url_val)
            if not u:
                continue
            row_to_url[r] = u
            raw_urls.append(u)
            host = (urlparse(u).netloc or "").lower()
            # Check TikTok URLs - expand short URLs to detect if they're valid video URLs
            if "tiktok.com" in host:
                expanded = tiktokmod.expand_tiktok_url(u)
                if tiktokmod.VID_RE.search(urlparse(expanded).path):
                    tiktok_rows.append(r)
            elif "instagram.com" in host:
                instagram_rows.append(r)

        total_urls = len(raw_urls)
        _log(f"Found {total_urls} URLs: {len(tiktok_rows)} TikTok, {len(instagram_rows)} Instagram")

        if total_urls == 0:
            _log("No URLs found in sheet")
            return

        # Fetch TikTok stats with progress
        tt_stats_by_url: Dict[str, Dict[str, str]] = {}
        tt_urls_unique = tiktokmod.tiktok_video_links(raw_urls)
        if tt_urls_unique:
            _log(f"Fetching {len(tt_urls_unique)} TikTok videos...")
            results = await run_tiktok(tt_urls_unique, show_progress=True)
            
            success_count = 0
            for (u, views, likes, comments, post_date, status) in results:
                if status == "ok":
                    tt_stats_by_url[u] = {"views": views, "likes": likes, "comments": comments, "date": post_date}
                    success_count += 1
            
            _log(f"TikTok: {success_count}/{len(tt_urls_unique)} successful")

        # Fetch Instagram stats with progress
        ig_stats_by_url: Dict[str, Dict[str, str]] = {}
        ig_urls_unique = []
        seen_ig = set()
        for r in instagram_rows:
            cu = igmod.canonicalize_instagram_url(row_to_url[r])
            if cu and cu not in seen_ig:
                ig_urls_unique.append(cu)
                seen_ig.add(cu)
        
        if ig_urls_unique:
            _log(f"Fetching {len(ig_urls_unique)} Instagram posts...")
            items = run_instagram(ig_urls_unique, show_progress=True)
            
            for item in items:
                plays, likes, comments, post_date = igmod.extract_impressions(item)
                username = igmod.extract_username(item)
                src = item.get("inputUrl") or item.get("url") or ""
                cu = igmod.canonicalize_instagram_url(src) if src else ""
                if cu:
                    ig_stats_by_url[cu] = {
                        "views": str(plays) if isinstance(plays, int) else "",
                        "likes": str(likes) if isinstance(likes, int) else "",
                        "comments": str(comments) if isinstance(comments, int) else "",
                        "username": username,
                        "date": post_date,
                    }
                    # Debug: log successful username extraction
                    if username:
                        _log(f"  ✓ Instagram username extracted: @{username}")
            
            _log(f"Instagram: {len(ig_stats_by_url)}/{len(ig_urls_unique)} successful")

        # Prepare column updates (use already-fetched values to avoid extra API calls)
        _log("Preparing sheet updates...")
        # Extract columns from values array instead of making individual cell() API calls
        # Only extract if column exists and only for the rows we're processing
        existing_names = [values[i][name_col - 1] if name_col > 0 and name_col <= len(values[i]) else "" for i in range(process_start_idx, process_end_idx)] if name_col else []
        existing_channels = [values[i][channel_col - 1] if channel_col > 0 and channel_col <= len(values[i]) else "" for i in range(process_start_idx, process_end_idx)] if channel_col else []
        existing_views = [values[i][views_col - 1] if views_col > 0 and views_col <= len(values[i]) else "" for i in range(process_start_idx, process_end_idx)] if views_col else []
        existing_likes = [values[i][likes_col - 1] if likes_col > 0 and likes_col <= len(values[i]) else "" for i in range(process_start_idx, process_end_idx)] if likes_col else []
        existing_comments = [values[i][comments_col - 1] if comments_col > 0 and comments_col <= len(values[i]) else "" for i in range(process_start_idx, process_end_idx)] if comments_col else []
        existing_impressions = [values[i][impressions_col - 1] if impressions_col > 0 and impressions_col <= len(values[i]) else "" for i in range(process_start_idx, process_end_idx)] if impressions_col else []
        existing_dates = [values[i][date_col - 1] if date_col > 0 and date_col <= len(values[i]) else "" for i in range(process_start_idx, process_end_idx)] if date_col else []

        new_names: List[str] = []
        new_channels: List[str] = []
        new_views: List[str] = []
        new_likes: List[str] = []
        new_comments: List[str] = []
        new_impressions: List[str] = []
        new_dates: List[str] = []
        changed_rows: List[bool] = []
        unsupported_count = 0
        
        # Process only the rows in the specified range
        for i, r in enumerate(range(process_start_idx + 1, process_end_idx + 1)):
            u = row_to_url.get(r, "")
            n = existing_names[i] if i < len(existing_names) else ""
            ch = existing_channels[i] if i < len(existing_channels) else ""
            v = existing_views[i] if i < len(existing_views) else ""
            l = existing_likes[i] if i < len(existing_likes) else ""
            c = existing_comments[i] if i < len(existing_comments) else ""
            
            # Store original values for override check
            orig_n = n
            orig_ch = ch
            orig_v = v
            orig_l = l
            orig_c = c
            
            # Helper to check if a value is empty
            def _is_empty(val: str) -> bool:
                return not (val or "").strip()
            
            # Check if URL is from an unsupported platform (YouTube, Facebook, X/Twitter)
            host = (urlparse(u).netloc or "").lower()
            is_unsupported = any(platform in host for platform in [
                "youtube.com", "youtu.be", 
                "facebook.com", "fb.com", "fb.watch",
                "twitter.com", "x.com"
            ])
            
            # Variables to store post date
            post_date = ""
            
            # If unsupported platform, keep all existing data and skip processing
            if is_unsupported:
                unsupported_count += 1
                # Just append existing values without modification
                if name_col:
                    new_names.append(n)
                if channel_col:
                    new_channels.append(ch)
                if views_col:
                    new_views.append(v)
                if likes_col:
                    new_likes.append(l)
                if comments_col:
                    new_comments.append(c)
                if impressions_col:
                    orig_imp = existing_impressions[i] if i < len(existing_impressions) else ""
                    new_impressions.append(orig_imp)
                if date_col:
                    orig_date = existing_dates[i] if i < len(existing_dates) else ""
                    new_dates.append(orig_date)
                changed_rows.append(False)
                continue
            
            # For TikTok, expand short URLs first to extract account name and fetch stats
            if "tiktok.com" in host:
                # Expand short URL to match the key used in tt_stats_by_url
                expanded_u = tiktokmod.expand_tiktok_url(u)
                
                # Extract account name from expanded URL if not already present
                if name_col and not n:
                    n = _extract_account_name(expanded_u)
                
                # Extract channel from URL if not already present
                if channel_col and not ch:
                    ch = _extract_channel(expanded_u)
                
                stats = tt_stats_by_url.get(expanded_u)
                if stats:
                    if views_col:
                        new_v = stats.get("views", v)
                        v = new_v if (override or _is_empty(orig_v)) else orig_v
                    if likes_col:
                        new_l = stats.get("likes", l)
                        l = new_l if (override or _is_empty(orig_l)) else orig_l
                    if comments_col:
                        new_c = stats.get("comments", c)
                        c = new_c if (override or _is_empty(orig_c)) else orig_c
                    # Get post date from TikTok stats
                    post_date = stats.get("date", "")
            elif "instagram.com" in host:
                # Extract account name from URL if not already present
                if name_col and not n:
                    n = _extract_account_name(u)
                
                # Extract channel from URL if not already present
                if channel_col and not ch:
                    ch = _extract_channel(u)
                
                stats = ig_stats_by_url.get(igmod.canonicalize_instagram_url(u))
                if stats:
                    # Use username from API if name is empty (override URL extraction)
                    if name_col and not n and stats.get("username"):
                        n = stats.get("username")
                    if views_col:
                        new_v = stats.get("views", v)
                        v = new_v if (override or _is_empty(orig_v)) else orig_v
                    if likes_col:
                        new_l = stats.get("likes", l)
                        l = new_l if (override or _is_empty(orig_l)) else orig_l
                    if comments_col:
                        new_c = stats.get("comments", c)
                        c = new_c if (override or _is_empty(orig_c)) else orig_c
                    # Get post date from Instagram stats
                    post_date = stats.get("date", "")
            else:
                # For other platforms (YouTube, Facebook, etc.), extract from URL
                if name_col and not n:
                    n = _extract_account_name(u)
                
                if channel_col and not ch:
                    ch = _extract_channel(u)
            
            # Calculate impressions
            orig_imp = existing_impressions[i] if i < len(existing_impressions) else ""
            if impressions_col:
                if (v or "").strip() == "":
                    imp = "unable"
                else:
                    imp = str(_to_int(v) + _to_int(l) + _to_int(c))
                # Only update impressions if override=True or original is empty
                if not override and not _is_empty(orig_imp):
                    imp = orig_imp
            else:
                imp = ""
            
            # Apply override logic for name and channel too
            if name_col:
                # Only update name if override=True or original is empty
                final_n = n if (override or _is_empty(orig_n)) else orig_n
                new_names.append(final_n)
            if channel_col:
                # Only update channel if override=True or original is empty
                final_ch = ch if (override or _is_empty(orig_ch)) else orig_ch
                new_channels.append(final_ch)
            if views_col:
                new_views.append(v)
            if likes_col:
                new_likes.append(l)
            if comments_col:
                new_comments.append(c)
            if impressions_col:
                new_impressions.append(imp)
            
            # Handle date column - use post date from video/post
            if date_col:
                orig_date = existing_dates[i] if i < len(existing_dates) else ""
                # Use the post_date from the video/post data
                # Only update if we have a post_date and (override=True or original is empty)
                if post_date and (override or _is_empty(orig_date)):
                    final_date = post_date
                else:
                    final_date = orig_date
                new_dates.append(final_date)
            
            was_changed = False
            if name_col and (final_n or "") != ((existing_names[i] if i < len(existing_names) else "") or ""):
                was_changed = True
            if channel_col and (final_ch or "") != ((existing_channels[i] if i < len(existing_channels) else "") or ""):
                was_changed = True
            if views_col and (v or "") != ((existing_views[i] if i < len(existing_views) else "") or ""):
                was_changed = True
            if likes_col and (l or "") != ((existing_likes[i] if i < len(existing_likes) else "") or ""):
                was_changed = True
            if comments_col and (c or "") != ((existing_comments[i] if i < len(existing_comments) else "") or ""):
                was_changed = True
            if impressions_col and (imp or "") != ((existing_impressions[i] if i < len(existing_impressions) else "") or ""):
                was_changed = True
            if date_col and (final_date or "") != ((existing_dates[i] if i < len(existing_dates) else "") or ""):
                was_changed = True
            
            changed_rows.append(bool(was_changed))

        # Write updates to sheet
        _log("Writing updates to sheet...")
        start = process_start_idx + 1  # Convert to 1-based row number
        end = process_end_idx
        
        try:
            # Only update columns that exist
            # Use value_input_option='USER_ENTERED' to interpret numbers as numbers, not text
            if name_col and new_names:
                rng_names = f"{_col_letter(name_col)}{start}:{_col_letter(name_col)}{end}"
                ws.update(rng_names, [[x] for x in new_names], value_input_option='USER_ENTERED')
            
            if channel_col and new_channels:
                rng_channels = f"{_col_letter(channel_col)}{start}:{_col_letter(channel_col)}{end}"
                ws.update(rng_channels, [[x] for x in new_channels], value_input_option='USER_ENTERED')
            
            if views_col and new_views:
                rng_views = f"{_col_letter(views_col)}{start}:{_col_letter(views_col)}{end}"
                ws.update(rng_views, [[x] for x in new_views], value_input_option='USER_ENTERED')
            
            if likes_col and new_likes:
                rng_likes = f"{_col_letter(likes_col)}{start}:{_col_letter(likes_col)}{end}"
                ws.update(rng_likes, [[x] for x in new_likes], value_input_option='USER_ENTERED')
            
            if comments_col and new_comments:
                rng_comments = f"{_col_letter(comments_col)}{start}:{_col_letter(comments_col)}{end}"
                ws.update(rng_comments, [[x] for x in new_comments], value_input_option='USER_ENTERED')
            
            if impressions_col and new_impressions:
                rng_impressions = f"{_col_letter(impressions_col)}{start}:{_col_letter(impressions_col)}{end}"
                ws.update(rng_impressions, [[x] for x in new_impressions], value_input_option='USER_ENTERED')
            
            if date_col and new_dates:
                rng_dates = f"{_col_letter(date_col)}{start}:{_col_letter(date_col)}{end}"
                ws.update(rng_dates, [[x] for x in new_dates], value_input_option='USER_ENTERED')

            # Update "last changed" column if present
            if last_changed_col:
                existing_changed = [values[i][last_changed_col - 1] if last_changed_col <= len(values[i]) else "" for i in range(process_start_idx, process_end_idx)]
                try:
                    now_human = datetime.now(timezone.utc).strftime("%-I:%M %b %d")
                except Exception:
                    now_human = datetime.now(timezone.utc).strftime("%I:%M %b %d").lstrip("0")
                last_changed_out: List[str] = []
                for i in range(0, end - start + 1):
                    last_changed_out.append(now_human if changed_rows[i] else (existing_changed[i] or ""))
                rng_changed = f"{_col_letter(last_changed_col)}{start}:{_col_letter(last_changed_col)}{end}"
                ws.update(rng_changed, [[x] for x in last_changed_out], value_input_option='USER_ENTERED')
        except Exception as e:
            _log(f"Error writing to sheet: {e}")
            raise

        # Summary
        num_changed = sum(changed_rows)
        if unsupported_count > 0:
            _log(f"Skipped {unsupported_count} unsupported platform(s) (YouTube/Facebook/X) - keeping existing data")
        _log(f"✓ Complete! Updated {num_changed}/{total_urls} rows")
        
    except ValueError as e:
        raise  # Re-raise validation errors
    except Exception as e:
        _log(f"Fatal error: {e}")
        raise RuntimeError(f"Failed to update sheet: {e}") from e



if __name__ == "__main__":
    asyncio.run(update_sheet_views_likes_comments())

def set_sheet_defaults(spreadsheet: str, worksheet: str) -> None:
    _save_config_defaults(spreadsheet, worksheet)

