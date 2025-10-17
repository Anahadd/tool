from TikTokApi import TikTokApi
import asyncio
import os
from pathlib import Path
from urllib.parse import urlparse
import re
from typing import Dict, List, Tuple
import gspread
from google.oauth2.service_account import Credentials
from apify_client import ApifyClient
import ig as igmod
import requests

VID_RE = re.compile(r"/video/(\d+)")
MS_TOKEN = os.environ.get("ms_token")

def clean_url(url: str) -> str:
    """
    Remove common prefixes that shouldn't be in URLs.
    Handles cases like @https://... when URLs are copied from social media.
    Also adds https:// protocol if missing for TikTok URLs.
    """
    url = url.strip()
    # Remove leading @ symbol (common when copying from social media)
    if url.startswith('@'):
        url = url[1:]
    
    # Add https:// protocol if missing for TikTok URLs
    if url and not url.startswith(('http://', 'https://')):
        # Check if it looks like a tiktok.com URL
        if url.startswith('tiktok.com') or url.startswith('www.tiktok.com'):
            url = 'https://' + url
    
    return url

def expand_tiktok_url(url: str, timeout: int = 10) -> str:
    """
    Expand TikTok short URLs (e.g., tiktok.com/t/XXX) to full URLs.
    Returns the expanded URL if successful, otherwise returns the original URL.
    """
    try:
        parsed = urlparse(url)
        host = (parsed.netloc or "").lower()
        
        # Check if this is a TikTok short URL (format: tiktok.com/t/XXX)
        if "tiktok.com" in host and parsed.path.startswith("/t/"):
            # Use proper headers to mimic a real browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Try GET request first (more reliable than HEAD for TikTok)
            try:
                response = requests.get(url, allow_redirects=True, timeout=timeout, headers=headers)
                expanded_url = response.url
            except Exception:
                # Fallback to HEAD request if GET fails
                response = requests.head(url, allow_redirects=True, timeout=timeout, headers=headers)
                expanded_url = response.url
            
            # Verify the expanded URL is a valid TikTok video URL
            if VID_RE.search(urlparse(expanded_url).path):
                return expanded_url
        
        # Return original URL if not a short URL or expansion failed
        return url
    except Exception as e:
        # Log error for debugging (to stderr so it doesn't interfere with output)
        import sys
        print(f"Warning: Failed to expand URL {url}: {e}", file=sys.stderr)
        # If anything goes wrong, return the original URL
        return url

def load_https_links(path="url.txt"):
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return []
    # Clean URLs and filter for https links
    result = []
    for ln in lines:
        cleaned = clean_url(ln)
        if cleaned.startswith("https"):
            result.append(cleaned)
    return result

def tiktok_video_links(urls):
    keep = []
    for u in urls:
        # Clean URL first (remove @ prefix, etc.), then expand short URLs
        cleaned = clean_url(u)
        expanded = expand_tiktok_url(cleaned)
        p = urlparse(expanded)
        host = (p.netloc or "").lower()
        if "tiktok.com" in host and VID_RE.search(p.path):
            keep.append(expanded)
    seen, out = set(), []
    for u in keep:
        if u not in seen:
            out.append(u); seen.add(u)
    return out

async def fetch_stats(api: TikTokApi, url: str, max_retries: int = 2):
    match = VID_RE.search(urlparse(url).path)
    if not match:
        return (url, "", "", "", "", "no_video_id")
    video_id = match.group(1)

    def to_int_str(value):
        try:
            if value is None or value == "":
                return "0"
            if isinstance(value, str):
                cleaned = value.replace(",", "")
                return str(int(float(cleaned))) if "." in cleaned else str(int(cleaned))
            return str(int(value))
        except Exception:
            return "0"
    
    def format_date(timestamp):
        """Convert Unix timestamp to MM/DD/YYYY format"""
        try:
            if timestamp and str(timestamp) != '0':
                from datetime import datetime
                ts_int = int(timestamp)
                # Validate timestamp is reasonable (after year 2000, before year 2100)
                if ts_int > 946684800 and ts_int < 4102444800:
                    dt = datetime.fromtimestamp(ts_int)
                    month = str(dt.month)
                    day = str(dt.day)
                    year = str(dt.year)
                    return f"{month}/{day}/{year}"
        except Exception:
            pass
        return ""

    def err_status(e: Exception) -> str:
        msg = str(e).replace(",", ";").replace("\n", " ").strip()
        return f"{type(e).__name__}:{msg}" if msg else type(e).__name__

    # Try multiple strategies with retries
    for attempt in range(max_retries + 1):
        try:
            # Strategy 1: Fetch by video ID (more reliable for some videos)
            info = await api.video(id=video_id).info()
            
            # Validate that we got useful data
            if isinstance(info, dict) and "stats" in info:
                stats = info.get("stats", {})
                # Check if we actually have view count data
                play_count = stats.get("playCount")
                if play_count is not None or attempt == max_retries:
                    # Extract creation date if available
                    create_time = info.get("createTime") or info.get("createtime") or ""
                    post_date = format_date(create_time)
                    return (
                        url,
                        to_int_str(play_count),
                        to_int_str(stats.get("diggCount")),
                        to_int_str(stats.get("commentCount")),
                        post_date,
                        "ok",
                    )
        except Exception as e_id:
            # If ID fetch fails, try URL-based fetch
            try:
                info = await api.video(url=url).info()
                
                # Validate that we got useful data
                if isinstance(info, dict) and "stats" in info:
                    stats = info.get("stats", {})
                    play_count = stats.get("playCount")
                    if play_count is not None or attempt == max_retries:
                        # Extract creation date if available
                        create_time = info.get("createTime") or info.get("createtime") or ""
                        post_date = format_date(create_time)
                        return (
                            url,
                            to_int_str(play_count),
                            to_int_str(stats.get("diggCount")),
                            to_int_str(stats.get("commentCount")),
                            post_date,
                            "ok",
                        )
            except Exception as e_url:
                # If this is the last attempt, return the error
                if attempt == max_retries:
                    return (url, "", "", "", "", err_status(e_url))
        
        # Wait a bit before retrying (exponential backoff)
        if attempt < max_retries:
            await asyncio.sleep(0.5 * (2 ** attempt))
    
    # Fallback if somehow we get here
    return (url, "", "", "", "", "no_data")

async def main():
    all_https = load_https_links("url.txt")
    tiktok_urls = tiktok_video_links(all_https)
    if not tiktok_urls:
        print("url,views,likes,comments,status")
        return
    async with TikTokApi() as api:
        await api.create_sessions(
            ms_tokens=[MS_TOKEN] if MS_TOKEN else None,
            num_sessions=1,
            sleep_after=1,
            headless=True,
            browser=os.getenv("TIKTOK_BROWSER", "chromium"),
        )
        results = await asyncio.gather(*(fetch_stats(api, u) for u in tiktok_urls))

    print("url,views,likes,comments,post_date,status")
    for row in results:
        print(",".join(row))

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

def _open_sheet(
    creds_path: str,
    spreadsheet_title: str,
    worksheet_name: str = "Impressions",
):
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    client = gspread.authorize(creds)
    ss = client.open(spreadsheet_title)
    try:
        ws = ss.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        ws = ss.get_worksheet(0)
    return ws

async def update_sheet_impressions():
    spreadsheet_title = os.getenv("GOOGLE_SHEETS_SPREADSHEET", "gen-lang-client-0071269503")
    worksheet_name = os.getenv("GOOGLE_SHEETS_WORKSHEET", "Impressions")
    creds_path = os.getenv(
        "GOOGLE_SHEETS_CREDS",
        str(Path(__file__).with_name("gen-lang-client-0071269503-018dc0a5ab5c.json")),
    )

    ws = _open_sheet(creds_path, spreadsheet_title, worksheet_name)
    values = ws.get_all_values()
    if not values:
        return
    headers = values[0]
    url_col = _col_index(headers, ["url", "link"])  # prefer a column titled URL
    imp_col = _col_index(headers, ["impressions", "impression", "plays", "views"])
    if url_col == 0 or imp_col == 0:
        print("Missing required columns: url and impressions")
        return

    row_to_url: Dict[int, str] = {}
    tiktok_rows: List[int] = []
    instagram_rows: List[int] = []
    raw_urls: List[str] = []

    for r in range(2, len(values) + 1):  # 1-based rows, skip header
        url_val = ws.cell(r, url_col).value or ""
        u = clean_url(url_val)
        if not u:
            continue
        row_to_url[r] = u
        raw_urls.append(u)
        host = (urlparse(u).netloc or "").lower()
        # Expand short TikTok URLs and check if it's a valid TikTok video URL
        if "tiktok.com" in host:
            expanded = expand_tiktok_url(u)
            if VID_RE.search(urlparse(expanded).path):
                tiktok_rows.append(r)
        elif "instagram.com" in host:
            instagram_rows.append(r)

    tt_views_by_url: Dict[str, str] = {}
    tt_urls_unique = tiktok_video_links(raw_urls)
    if tt_urls_unique:
        async with TikTokApi() as api:
            await api.create_sessions(
                ms_tokens=[MS_TOKEN] if MS_TOKEN else None,
                num_sessions=1,
                sleep_after=1,
                headless=True,
                browser=os.getenv("TIKTOK_BROWSER", "chromium"),
            )
            results = await asyncio.gather(*(fetch_stats(api, u) for u in tt_urls_unique))
        for (u, views, _likes, _comments, _post_date, status) in results:
            tt_views_by_url[u] = views if status == "ok" else ""

    ig_urls_unique = []
    seen_ig = set()
    for r in instagram_rows:
        cu = igmod.canonicalize_instagram_url(row_to_url[r])
        if cu and cu not in seen_ig:
            ig_urls_unique.append(cu)
            seen_ig.add(cu)

    ig_views_by_url: Dict[str, str] = {}
    if ig_urls_unique:
        client = ApifyClient(igmod.API_TOKEN)
        run_input = {
            "directUrls": ig_urls_unique,
            "resultsType": "posts",
            "resultsLimit": 1,
            "addParentData": False,
        }
        run = client.actor(igmod.ACTOR_ID).call(run_input=run_input)
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            plays, _likes, _comments = igmod.extract_impressions(item)
            src = item.get("inputUrl") or item.get("url") or ""
            cu = igmod.canonicalize_instagram_url(src) if src else ""
            if cu:
                ig_views_by_url[cu] = str(plays) if isinstance(plays, int) else ""

    last_row = len(values)
    existing_imp = [ws.cell(r, imp_col).value for r in range(2, last_row + 1)]
    new_imp: List[str] = []
    for i, r in enumerate(range(2, last_row + 1)):
        u = row_to_url.get(r, "")
        v = existing_imp[i] or ""
        host = (urlparse(u).netloc or "").lower()
        if "tiktok.com" in host:
            v = tt_views_by_url.get(u, v)
        elif "instagram.com" in host:
            v = ig_views_by_url.get(igmod.canonicalize_instagram_url(u), v)
        new_imp.append(v)

    start = 2
    end = last_row
    col_letter = _col_letter(imp_col)
    rng = f"{col_letter}{start}:{col_letter}{end}"
    ws.update(rng, [[x] for x in new_imp])


if __name__ == "__main__":
    asyncio.run(update_sheet_impressions())
