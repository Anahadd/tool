#!/usr/bin/env python3
"""Test URL processing to identify issues"""
import sys
from main import clean_url, expand_tiktok_url, tiktok_video_links
from pathlib import Path

# Read test URLs
test_urls = Path("test_urls.txt").read_text().strip().split("\n")

print(f"Testing {len(test_urls)} URLs...\n", file=sys.stderr)

for i, url in enumerate(test_urls, 1):
    print(f"\n{i}. Original: {url}", file=sys.stderr)
    
    # Step 1: Clean URL
    cleaned = clean_url(url)
    print(f"   Cleaned:  {cleaned}", file=sys.stderr)
    
    # Step 2: Expand short URL
    try:
        expanded = expand_tiktok_url(cleaned, timeout=5)
        print(f"   Expanded: {expanded}", file=sys.stderr)
    except Exception as e:
        print(f"   ❌ Expand failed: {e}", file=sys.stderr)
        expanded = cleaned
    
    # Step 3: Check if it's a valid TikTok video
    valid = tiktok_video_links([expanded])
    if valid:
        print(f"   ✅ Valid TikTok video URL", file=sys.stderr)
    else:
        print(f"   ❌ NOT a valid TikTok video URL", file=sys.stderr)

# Now test the full pipeline
print("\n" + "="*60, file=sys.stderr)
print("Testing full pipeline...", file=sys.stderr)
print("="*60 + "\n", file=sys.stderr)

valid_urls = tiktok_video_links(test_urls)
print(f"\n✅ Found {len(valid_urls)} valid TikTok video URLs out of {len(test_urls)}", file=sys.stderr)

if len(valid_urls) < len(test_urls):
    print(f"⚠️  {len(test_urls) - len(valid_urls)} URLs were filtered out", file=sys.stderr)

