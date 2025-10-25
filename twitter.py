"""
X (Twitter) integration for fetching tweet engagement metrics
Uses Twitter API v2
"""
import os
import re
from urllib.parse import urlparse
from typing import Optional, Tuple, Dict
import requests
from requests_oauthlib import OAuth1

# Twitter API configuration
API_KEY = os.environ.get("TWITTER_API_KEY", "")
API_SECRET = os.environ.get("TWITTER_API_SECRET", "")
ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN", "")
ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", "")
BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN", "")

# API endpoints
API_V2_BASE = "https://api.twitter.com/2"
API_V1_BASE = "https://api.twitter.com/1.1"

# Regex patterns for extracting tweet IDs
TWEET_ID_PATTERNS = [
    re.compile(r'twitter\.com/[^/]+/status/(\d+)'),
    re.compile(r'x\.com/[^/]+/status/(\d+)'),
]

def clean_url(url: str) -> str:
    """
    Remove common prefixes that shouldn't be in URLs.
    Handles cases like @https://... when URLs are copied from social media.
    """
    url = url.strip()
    # Remove leading @ symbol
    if url.startswith('@'):
        url = url[1:]
    
    # Add https:// protocol if missing
    if url and not url.startswith(('http://', 'https://')):
        if 'twitter.com' in url or 'x.com' in url:
            url = 'https://' + url
    
    return url

def extract_tweet_id(url: str) -> Optional[str]:
    """
    Extract tweet ID from various URL formats.
    
    Supports:
    - https://twitter.com/username/status/TWEET_ID
    - https://x.com/username/status/TWEET_ID
    - With query parameters like ?s=46&t=...
    
    Args:
        url: Twitter/X URL
        
    Returns:
        Tweet ID if found, None otherwise
    """
    url = clean_url(url)
    
    # Try regex patterns
    for pattern in TWEET_ID_PATTERNS:
        match = pattern.search(url)
        if match:
            tweet_id = match.group(1)
            return tweet_id
    
    return None

def is_twitter_url(url: str) -> bool:
    """Check if a URL is a Twitter/X tweet URL."""
    url = clean_url(url)
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    return ("twitter.com" in host or "x.com" in host) and "/status/" in url

def canonicalize_twitter_url(url: str) -> Optional[str]:
    """
    Convert any Twitter URL to a canonical format.
    Returns the canonical URL if valid, None otherwise.
    """
    tweet_id = extract_tweet_id(url)
    if tweet_id:
        return f"https://x.com/i/status/{tweet_id}"
    return None

def fetch_tweet_stats_v2(tweet_id: str, bearer_token: Optional[str] = None) -> Tuple[str, str, str, str, str, str]:
    """
    Fetch statistics for a tweet using Twitter API v2.
    
    Args:
        tweet_id: Twitter tweet ID
        bearer_token: Twitter API v2 Bearer Token
        
    Returns:
        Tuple of (tweet_id, views, likes, retweets, replies, status)
    """
    if not bearer_token:
        bearer_token = BEARER_TOKEN
    
    if not bearer_token:
        return (tweet_id, "", "", "", "", "no_bearer_token")
    
    try:
        url = f"{API_V2_BASE}/tweets/{tweet_id}"
        params = {
            "tweet.fields": "public_metrics",
        }
        headers = {
            "Authorization": f"Bearer {bearer_token}"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        # Handle rate limit
        if response.status_code == 429:
            return (tweet_id, "", "", "", "", "rate_limited")
        
        # Handle unauthorized
        if response.status_code == 401:
            return (tweet_id, "", "", "", "", "unauthorized")
        
        # Handle not found
        if response.status_code == 404:
            return (tweet_id, "", "", "", "", "not_found")
        
        # Handle other errors
        if response.status_code != 200:
            return (tweet_id, "", "", "", "", f"http_error_{response.status_code}")
        
        data = response.json()
        
        # Check if tweet data exists
        if "data" not in data:
            return (tweet_id, "", "", "", "", "no_data")
        
        # Extract metrics
        tweet_data = data["data"]
        metrics = tweet_data.get("public_metrics", {})
        
        # Note: View count is not available in free API tier
        views = ""  # Views require elevated access
        likes = str(metrics.get("like_count", ""))
        retweets = str(metrics.get("retweet_count", ""))
        replies = str(metrics.get("reply_count", ""))
        
        return (tweet_id, views, likes, retweets, replies, "ok")
        
    except requests.Timeout:
        return (tweet_id, "", "", "", "", "timeout")
    except requests.RequestException:
        return (tweet_id, "", "", "", "", "request_error")
    except Exception as e:
        return (tweet_id, "", "", "", "", f"error:{type(e).__name__}")

def fetch_tweet_stats_by_url(url: str, bearer_token: Optional[str] = None) -> Tuple[str, str, str, str, str, str]:
    """
    Fetch statistics for a tweet by URL.
    
    Args:
        url: Twitter/X tweet URL
        bearer_token: Twitter API v2 Bearer Token
        
    Returns:
        Tuple of (url, views, likes, retweets, replies, status)
    """
    tweet_id = extract_tweet_id(url)
    
    if not tweet_id:
        return (url, "", "", "", "", "invalid_url")
    
    tid, views, likes, retweets, replies, status = fetch_tweet_stats_v2(tweet_id, bearer_token)
    
    return (url, views, likes, retweets, replies, status)

def twitter_links(urls: list) -> list:
    """
    Filter and return only valid Twitter/X tweet URLs from a list of URLs.
    Also canonicalizes the URLs.
    
    Args:
        urls: List of URLs to filter
        
    Returns:
        List of canonical Twitter URLs
    """
    result = []
    seen = set()
    
    for url in urls:
        if not is_twitter_url(url):
            continue
        
        canonical = canonicalize_twitter_url(url)
        if canonical and canonical not in seen:
            result.append(canonical)
            seen.add(canonical)
    
    return result

# Note: The provided credentials (API Key and Secret) are OAuth 1.0a consumer credentials
# To use Twitter API, you also need:
# 1. Bearer Token (for API v2 - easiest), OR
# 2. Access Token + Access Token Secret (for OAuth 1.0a)
# 
# Get your Bearer Token from: https://developer.twitter.com/en/portal/projects-and-apps

