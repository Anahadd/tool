#!/usr/bin/env python3
"""Test fetching stats from sample URLs"""
import asyncio
import sys
from pathlib import Path
from TikTokApi import TikTokApi
import os
import main as tiktokmod

async def test_fetch():
    # Test with a few URLs
    test_urls = [
        "https://www.tiktok.com/t/ZTMmxen3C/",  # Short URL
        "https://www.tiktok.com/@jaydenwins/video/7564116910376242446",  # Full URL
        "@https://www.tiktok.com/t/ZTMMEg8dF/",  # URL with @ prefix
    ]
    
    print("Testing URL processing and stats fetching...\n", file=sys.stderr)
    
    # Clean and expand URLs first
    processed_urls = []
    for url in test_urls:
        cleaned = tiktokmod.clean_url(url)
        expanded = tiktokmod.expand_tiktok_url(cleaned, timeout=5)
        processed_urls.append(expanded)
        print(f"Original: {url}", file=sys.stderr)
        print(f"  → {expanded}\n", file=sys.stderr)
    
    # Now try to fetch stats
    print("Creating TikTok API session...", file=sys.stderr)
    try:
        async with TikTokApi() as api:
            await api.create_sessions(
                ms_tokens=[tiktokmod.MS_TOKEN] if tiktokmod.MS_TOKEN else None,
                num_sessions=1,
                sleep_after=1,
                headless=True,
                browser=os.getenv("TIKTOK_BROWSER", "chromium"),
                timeout=int(os.getenv("PLAYWRIGHT_TIMEOUT", "60000")),
            )
            print("✅ Session created!\n", file=sys.stderr)
            
            print("Fetching stats...", file=sys.stderr)
            results = await asyncio.gather(
                *(tiktokmod.fetch_stats(api, url) for url in processed_urls),
                return_exceptions=True
            )
            
            print("\nResults:", file=sys.stderr)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"{i+1}. ❌ Error: {result}", file=sys.stderr)
                else:
                    url, views, likes, comments, date, status = result
                    print(f"{i+1}. Status: {status}, Views: {views}, Likes: {likes}", file=sys.stderr)
            
            success_count = sum(1 for r in results if not isinstance(r, Exception) and r[5] == "ok")
            print(f"\n✅ {success_count}/{len(results)} URLs fetched successfully", file=sys.stderr)
            
            return success_count == len(results)
            
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_fetch())
    sys.exit(0 if result else 1)

