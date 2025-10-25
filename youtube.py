"""
YouTube integration for fetching video statistics
Uses YouTube Data API v3
"""
import os
import re
from urllib.parse import urlparse, parse_qs
from typing import Optional, Tuple
import requests

# YouTube API configuration
API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
API_BASE_URL = "https://www.googleapis.com/youtube/v3/videos"

# Regex patterns for extracting video IDs
VIDEO_ID_PATTERNS = [
    re.compile(r'youtube\.com/watch\?v=([^&]+)'),
    re.compile(r'youtube\.com/shorts/([^?]+)'),
    re.compile(r'youtu\.be/([^?]+)'),
    re.compile(r'youtube\.com/embed/([^?]+)'),
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
    
    # Add https:// protocol if missing for YouTube URLs
    if url and not url.startswith(('http://', 'https://')):
        if 'youtube.com' in url or 'youtu.be' in url:
            url = 'https://' + url
    
    return url

def extract_video_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from various URL formats.
    
    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtube.com/shorts/VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    
    Args:
        url: YouTube URL
        
    Returns:
        Video ID if found, None otherwise
    """
    url = clean_url(url)
    
    # Try regex patterns
    for pattern in VIDEO_ID_PATTERNS:
        match = pattern.search(url)
        if match:
            video_id = match.group(1)
            # Remove any additional parameters
            if '&' in video_id:
                video_id = video_id.split('&')[0]
            return video_id
    
    # Try parsing query parameters (for watch?v= URLs)
    try:
        parsed = urlparse(url)
        if parsed.query:
            params = parse_qs(parsed.query)
            if 'v' in params:
                return params['v'][0]
    except Exception:
        pass
    
    return None

def is_youtube_url(url: str) -> bool:
    """Check if a URL is a YouTube video URL."""
    url = clean_url(url)
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    return "youtube.com" in host or "youtu.be" in host

def canonicalize_youtube_url(url: str) -> Optional[str]:
    """
    Convert any YouTube URL to a canonical format.
    Returns the canonical URL if valid, None otherwise.
    """
    video_id = extract_video_id(url)
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    return None

def fetch_video_stats(video_id: str, api_key: Optional[str] = None) -> Tuple[str, str, str, str, str]:
    """
    Fetch statistics for a YouTube video.
    
    Args:
        video_id: YouTube video ID
        api_key: YouTube API key (uses env var if not provided)
        
    Returns:
        Tuple of (video_id, view_count, like_count, comment_count, status)
        status is one of: "ok", "error", "not_found", "quota_exceeded"
    """
    if not api_key:
        api_key = API_KEY
    
    if not api_key:
        return (video_id, "", "", "", "no_api_key")
    
    try:
        params = {
            "part": "statistics",
            "id": video_id,
            "key": api_key
        }
        
        response = requests.get(API_BASE_URL, params=params, timeout=10)
        
        # Handle quota exceeded
        if response.status_code == 403:
            error_data = response.json()
            if "quotaExceeded" in str(error_data):
                return (video_id, "", "", "", "quota_exceeded")
        
        # Handle other errors
        if response.status_code != 200:
            return (video_id, "", "", "", f"http_error_{response.status_code}")
        
        data = response.json()
        
        # Check if video was found
        if not data.get("items"):
            return (video_id, "", "", "", "not_found")
        
        # Extract statistics
        item = data["items"][0]
        stats = item.get("statistics", {})
        
        view_count = stats.get("viewCount", "")
        like_count = stats.get("likeCount", "")
        comment_count = stats.get("commentCount", "")
        
        return (video_id, view_count, like_count, comment_count, "ok")
        
    except requests.Timeout:
        return (video_id, "", "", "", "timeout")
    except requests.RequestException as e:
        return (video_id, "", "", "", f"request_error")
    except Exception as e:
        return (video_id, "", "", "", f"error:{type(e).__name__}")

def fetch_stats_by_url(url: str, api_key: Optional[str] = None) -> Tuple[str, str, str, str, str]:
    """
    Fetch statistics for a YouTube video by URL.
    
    Args:
        url: YouTube video URL
        api_key: YouTube API key (uses env var if not provided)
        
    Returns:
        Tuple of (url, view_count, like_count, comment_count, status)
    """
    video_id = extract_video_id(url)
    
    if not video_id:
        return (url, "", "", "", "invalid_url")
    
    vid_id, views, likes, comments, status = fetch_video_stats(video_id, api_key)
    
    return (url, views, likes, comments, status)

def youtube_video_links(urls: list[str]) -> list[str]:
    """
    Filter and return only valid YouTube video URLs from a list of URLs.
    Also canonicalizes the URLs.
    
    Args:
        urls: List of URLs to filter
        
    Returns:
        List of canonical YouTube URLs
    """
    result = []
    seen = set()
    
    for url in urls:
        if not is_youtube_url(url):
            continue
        
        canonical = canonicalize_youtube_url(url)
        if canonical and canonical not in seen:
            result.append(canonical)
            seen.add(canonical)
    
    return result

