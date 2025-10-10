from apify_client import ApifyClient
from pathlib import Path
from urllib.parse import urlparse, urlunparse
import json, os, sys

API_TOKEN = os.getenv("APIFY_TOKEN", "")
ACTOR_ID = os.getenv("APIFY_ACTOR_ID", "shu8hvrXbJbY3Eb9W")  # Instagram Scraper


def clean_url(url: str) -> str:
    """
    Remove common prefixes that shouldn't be in URLs.
    Handles cases like @https://... when URLs are copied from social media.
    Also adds https:// protocol if missing for social media URLs.
    """
    url = url.strip()
    # Remove leading @ symbol (common when copying from social media)
    if url.startswith('@'):
        url = url[1:]
    
    # Add https:// protocol if missing for social media URLs
    if url and not url.startswith(('http://', 'https://')):
        # Check if it looks like a social media URL
        if any(domain in url for domain in ['tiktok.com', 'instagram.com']):
            url = 'https://' + url
    
    return url


def canonicalize_instagram_url(u: str) -> str:
    """Strip query/fragments & trailing slash for a stable directUrl."""
    # Clean the URL first (remove @ prefix, etc.)
    u = clean_url(u)
    p = urlparse(u)
    if "instagram.com" not in p.netloc.lower():
        return ""
    canonical = p._replace(query="", fragment="")
    return urlunparse(canonical).rstrip("/")


def load_instagram_urls(path="url.txt"):
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        print("url.txt not found", file=sys.stderr)
        return []
    urls, seen = [], set()
    for ln in lines:
        u = canonicalize_instagram_url(ln.strip())
        if not u:
            continue
        if u not in seen:
            urls.append(u)
            seen.add(u)
    return urls


def first_num(vals):
    for v in vals:
        if isinstance(v, (int, float)) and v >= 0:
            return int(v)
    return None


def extract_username(item: dict) -> str:
    """
    Extract the Instagram username from an Apify response item.
    Tries multiple field names that Apify might return.
    Returns empty string if username not found.
    """
    # Try common username field names from Apify Instagram scraper
    username_candidates = [
        item.get("ownerUsername"),
        item.get("username"),
        item.get("owner_username"),
        item.get("displayUrl"),  # Sometimes contains username
    ]
    
    # Try nested owner object
    owner = item.get("owner")
    if isinstance(owner, dict):
        username_candidates.extend([
            owner.get("username"),
            owner.get("ownerUsername"),
        ])
    
    display_url = item.get("displayUrl") or ""
    if display_url and "/" in display_url:
        parts = display_url.split("/")
        for part in parts:
            if part and not part.startswith("http") and part not in ["www.instagram.com", "instagram.com", "reel", "p", "tv"]:
                username_candidates.append(part)
    
    for username in username_candidates:
        if username and isinstance(username, str) and username.strip():
            clean = username.strip().lstrip("@")
            if clean and not clean.startswith("http"):
                return clean
    
    return ""


def extract_impressions(item: dict):
    """
    Returns (plays, likes, comments) where any can be None if unavailable/hidden.
    - plays: prefers top-level video counts; for Sidecar, also checks child video posts.
    - likes: -1 means hidden -> treat as None; try known fallbacks.
    - comments: uses commentsCount, then edge dicts, then latestComments length.
    """
    plays_candidates = [
        item.get("videoPlayCount"),
        item.get("videoViewCount"),
        item.get("playCount"),
        item.get("video_view_count"),
    ]
    if item.get("type") == "Sidecar" and item.get("childPosts"):
        for child in item["childPosts"]:
            plays_candidates += [child.get("videoPlayCount"), child.get("videoViewCount")]

    plays = first_num(plays_candidates)

    likes_candidates = [
        (None if item.get("likesCount") == -1 else item.get("likesCount")),
        (item.get("edge_liked_by") or {}).get("count") if isinstance(item.get("edge_liked_by"), dict) else None,
        item.get("like_count"),
        item.get("previewLikeCount"),
    ]
    likes = first_num(likes_candidates)

    comments_candidates = [
        item.get("commentsCount"),
        (item.get("edge_media_to_comment") or {}).get("count") if isinstance(item.get("edge_media_to_comment"), dict) else None,
        len(item.get("latestComments") or []),
    ]
    comments = first_num(comments_candidates)
    if comments is None:
        comments = 0  # reasonable default

    return plays, likes, comments


def fmt(n):
    return f"{n:,}" if isinstance(n, int) else "N/A"


def label_for(item: dict):
    return item.get("shortCode") or item.get("shortcode") or item.get("url") or item.get("inputUrl") or "post"


def print_impressions(item: dict):
    plays, likes, comments = extract_impressions(item)
    lab = label_for(item)
    src = item.get("inputUrl") or item.get("url") or ""
    print(f"{lab}: {fmt(plays)} plays | {fmt(likes)} likes | {fmt(comments)} comments")
    if src:
        print(f"  ↳ {src}")
 
def main():
    urls = load_instagram_urls("url.txt")
    if not urls:
        print("No Instagram URLs found in url.txt")
        return
    
    if not API_TOKEN:
        print("Error: APIFY_TOKEN environment variable not set.", file=sys.stderr)
        print("Get your token at https://console.apify.com/account/integrations", file=sys.stderr)
        sys.exit(1)

    client = ApifyClient(API_TOKEN)
    run_input = {
        "directUrls": urls,
        "resultsType": "posts",
        "resultsLimit": 1,
        "addParentData": False,
    }

    run = client.actor(ACTOR_ID).call(run_input=run_input)

    print("=== IMPRESSIONS ===")
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        print_impressions(item)


if __name__ == "__main__":
    main()
