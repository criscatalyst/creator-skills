#!/usr/bin/env python3
"""
YouTube Outlier Detection using YouTube Data API v3.

Given a topic, finds the highest-performing videos on YouTube — ranked by
outlier score = video views / channel median views. A 10x outlier means the
video did 10 times the channel's normal performance, which is a stronger viral
signal than raw view count.

Pipeline:
- YouTube search (English audio only, medium duration → no shorts, < max_days old)
- For each unique channel found, sample recent videos to compute median views
- outlier_score = views / median
- Sort by outlier_score, take top N, fetch transcripts, write JSON

Free tier: 10,000 quota units/day. A single-topic run uses ~300 units.

Usage:
    python outlier_detector.py --terms "fitness for busy parents"
    python outlier_detector.py --terms "personal finance" "investing for beginners"
    python outlier_detector.py --terms "claude code" --skip_transcripts
    python outlier_detector.py --terms "cooking" --max_days 14 --min_views 50000
"""

import os
import sys
import json
import time
import datetime
import argparse
import html
import re
import statistics
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from googleapiclient.discovery import build

# Load .env from the script's own directory, then from ~/.config/outliers/.env
# (the second one survives plugin updates, which replace the skill directory)
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
load_dotenv(os.path.expanduser("~/.config/outliers/.env"))

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Unicode script ranges we drop from titles to enforce English-language results.
# This is a language filter, not a niche filter.
NON_LATIN_SCRIPTS = (
    "CJK", "HIRAGANA", "KATAKANA", "HANGUL", "ARABIC", "DEVANAGARI",
    "BENGALI", "TAMIL", "TELUGU", "THAI", "HEBREW", "CYRILLIC", "GREEK",
    "ARMENIAN", "GEORGIAN", "ETHIOPIC", "KHMER", "LAO", "MYANMAR",
)


def has_non_latin_script(text):
    """Return True if the title contains characters from a non-Latin script."""
    for char in text:
        if not char.isalpha():
            continue
        try:
            name = unicodedata.name(char, "")
        except ValueError:
            continue
        if any(script in name for script in NON_LATIN_SCRIPTS):
            return True
    return False


def get_channel_median_views(youtube, channel_id, max_videos=30, cache=None):
    """Median view count for a channel's recent videos. Used as the baseline."""
    if cache is not None and channel_id in cache:
        return cache[channel_id]

    try:
        # UC... → UU... gives us the uploads playlist
        uploads_playlist_id = "UU" + channel_id[2:]

        pl_response = youtube.playlistItems().list(
            playlistId=uploads_playlist_id,
            part="contentDetails",
            maxResults=max_videos
        ).execute()

        video_ids = [
            item["contentDetails"]["videoId"]
            for item in pl_response.get("items", [])
        ]

        if not video_ids:
            if cache is not None:
                cache[channel_id] = 1.0
            return 1.0

        stats_response = youtube.videos().list(
            id=",".join(video_ids),
            part="statistics"
        ).execute()

        view_counts = []
        for item in stats_response.get("items", []):
            vc = int(item["statistics"].get("viewCount", 0))
            if vc > 0:
                view_counts.append(vc)

        median = statistics.median(view_counts) if view_counts else 1.0

        if cache is not None:
            cache[channel_id] = median

        return median

    except Exception as e:
        print(f"    Warning: could not get median for channel {channel_id}: {str(e)[:80]}")
        if cache is not None:
            cache[channel_id] = 1.0
        return 1.0


def _parse_iso_duration(duration_str):
    """Parse ISO 8601 duration (PT#H#M#S) to seconds."""
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if not match:
        return 0
    h = int(match.group(1) or 0)
    m = int(match.group(2) or 0)
    s = int(match.group(3) or 0)
    return h * 3600 + m * 60 + s


def search_topic(youtube, query, max_results, min_views, published_after,
                 channel_videos, channel_cache, exclude_terms):
    """Search YouTube for videos on a topic, score them, return list of dicts."""
    try:
        search_params = {
            "q": query,
            "type": "video",
            "part": "snippet",
            "maxResults": min(max_results, 50),
            "order": "viewCount",
            "relevanceLanguage": "en",
            "regionCode": "US",
            "videoDuration": "medium",  # 4-20 min — excludes shorts
        }
        if published_after:
            search_params["publishedAfter"] = published_after

        search_response = youtube.search().list(**search_params).execute()
        items = search_response.get("items", [])
        if not items:
            return []

        video_ids = []
        snippet_map = {}
        for item in items:
            vid = item["id"]["videoId"]
            video_ids.append(vid)
            snippet_map[vid] = item["snippet"]

        stats_response = youtube.videos().list(
            id=",".join(video_ids),
            part="statistics,contentDetails,snippet"
        ).execute()

        video_stats = {item["id"]: item for item in stats_response.get("items", [])}

        unique_channels = {snippet_map[v].get("channelId", "")
                           for v in video_ids if snippet_map.get(v, {}).get("channelId")}
        print(f"    Computing channel medians for {len(unique_channels)} channels...")
        for ch_id in unique_channels:
            get_channel_median_views(youtube, ch_id,
                                     max_videos=channel_videos, cache=channel_cache)

        videos = []
        skipped_non_latin = skipped_non_english = skipped_gaming = skipped_excluded = 0

        for vid in video_ids:
            snippet = snippet_map.get(vid, {})
            stats_item = video_stats.get(vid)
            if not stats_item:
                continue

            title = html.unescape(snippet.get("title", ""))

            if has_non_latin_script(title):
                skipped_non_latin += 1
                continue

            video_snippet = stats_item.get("snippet", {})
            audio_lang = (video_snippet.get("defaultAudioLanguage")
                          or video_snippet.get("defaultLanguage")
                          or "")
            if audio_lang and not audio_lang.lower().startswith("en"):
                skipped_non_english += 1
                continue

            if video_snippet.get("categoryId") == "20":  # Gaming
                skipped_gaming += 1
                continue

            if exclude_terms:
                title_lower = title.lower()
                if any(term.lower() in title_lower for term in exclude_terms):
                    skipped_excluded += 1
                    continue

            stats = stats_item.get("statistics", {})
            view_count = int(stats.get("viewCount", 0))
            if view_count < min_views:
                continue

            duration_seconds = _parse_iso_duration(
                stats_item.get("contentDetails", {}).get("duration", "PT0S")
            )
            if duration_seconds < 61:
                continue

            channel_id = snippet.get("channelId", "")
            channel_median = channel_cache.get(channel_id, 1.0) if channel_cache else 1.0
            outlier_score = round(view_count / channel_median, 2) if channel_median > 0 else 0

            thumbnails = snippet.get("thumbnails", {})
            thumb_url = (
                thumbnails.get("high", {}).get("url") or
                thumbnails.get("medium", {}).get("url") or
                thumbnails.get("default", {}).get("url") or
                f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg"
            )

            published_at = snippet.get("publishedAt", "")
            date_str = ""
            days_old = 999
            if published_at:
                try:
                    pub_date = datetime.datetime.fromisoformat(
                        published_at.replace("Z", "+00:00")
                    )
                    date_str = pub_date.strftime("%Y%m%d")
                    days_old = (datetime.datetime.now(datetime.timezone.utc) - pub_date).days
                except Exception:
                    pass

            videos.append({
                "video_id": vid,
                "title": title,
                "url": f"https://www.youtube.com/watch?v={vid}",
                "view_count": view_count,
                "like_count": int(stats.get("likeCount", 0)),
                "comment_count": int(stats.get("commentCount", 0)),
                "duration": duration_seconds,
                "channel_name": snippet.get("channelTitle", ""),
                "channel_id": channel_id,
                "channel_median_views": int(channel_median),
                "thumbnail_url": thumb_url,
                "date": date_str,
                "days_old": days_old,
                "outlier_score": outlier_score,
                "source": f"youtube: {query}",
            })

        dropped = (skipped_non_latin or skipped_non_english
                   or skipped_gaming or skipped_excluded)
        if dropped:
            print(f"    Filters: {skipped_non_latin} non-Latin, "
                  f"{skipped_non_english} non-English, "
                  f"{skipped_gaming} gaming, "
                  f"{skipped_excluded} excluded by --exclude_terms")

        return videos

    except Exception as e:
        print(f"  YouTube API error: {str(e)[:150]}")
        return []


def fetch_transcript(video_id):
    """Fetch transcript using youtube-transcript-api v1.x instance API."""
    if not video_id:
        return None
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        time.sleep(1)  # rate limit
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id)
        return ' '.join(snippet.text for snippet in fetched)
    except Exception as e:
        print(f"    [transcript] failed: {str(e)[:100]}")
        return None


def process_outlier(outlier, index, total, skip_transcripts):
    """Fetch transcript for one outlier (parallelized in main)."""
    title_short = outlier['title'][:50] + ("..." if len(outlier['title']) > 50 else "")
    print(f"\n  [{index}/{total}] {title_short}")

    if skip_transcripts:
        outlier["transcript_excerpt"] = ""
    else:
        print(f"    Fetching transcript...")
        transcript = fetch_transcript(outlier["video_id"])
        if transcript:
            print(f"    Got transcript ({len(transcript)} chars)")
            outlier["transcript_excerpt"] = transcript[:8000]
        else:
            outlier["transcript_excerpt"] = ""

    print(f"    Done")
    return outlier


def save_results_json(outliers, output_path):
    """Save results to a JSON file."""
    output_data = {
        "generated_at": datetime.datetime.now().isoformat(),
        "total_outliers": len(outliers),
        "outliers": [
            {
                "outlier_score": o["outlier_score"],
                "title": o["title"],
                "url": o["url"],
                "thumbnail_url": o["thumbnail_url"],
                "view_count": o["view_count"],
                "like_count": o.get("like_count", 0),
                "comment_count": o.get("comment_count", 0),
                "duration_minutes": round(o.get("duration", 0) / 60, 1),
                "days_old": o.get("days_old", None),
                "channel_name": o["channel_name"],
                "channel_median_views": o.get("channel_median_views", 0),
                "transcript_excerpt": o.get("transcript_excerpt", ""),
                "date": o.get("date", ""),
                "source": o.get("source", ""),
            }
            for o in outliers
        ]
    }
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    return output_path


def print_summary(outliers):
    """Print a readable summary of top outliers."""
    print("\n" + "=" * 70)
    print("  TOP OUTLIERS")
    print("=" * 70)
    for i, o in enumerate(outliers, 1):
        print(f"\n  #{i}  [{o['outlier_score']}x] {o['title']}")
        print(f"       {o['channel_name']} | {o['view_count']:,} views | "
              f"{o.get('days_old', '?')}d old")
        print(f"       {o['url']}")
    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="YouTube outlier detection — top performers for a given topic, "
                    "ranked by views ÷ channel median."
    )
    parser.add_argument("--terms", nargs="+", required=True,
                        help="One or more topic strings to search YouTube for. Required.")
    parser.add_argument("--results", type=int, default=50,
                        help="Results per query (max 50, API limit)")
    parser.add_argument("--min_views", type=int, default=10000,
                        help="Minimum view count (default: 10,000)")
    parser.add_argument("--max_days", type=int, default=30,
                        help="Max age in days (default: 30)")
    parser.add_argument("--min_score", type=float, default=1.5,
                        help="Minimum outlier score = views/channel_median (default: 1.5)")
    parser.add_argument("--limit", type=int, default=10,
                        help="Max outliers to keep (default: 10)")
    parser.add_argument("--channel-videos", type=int, default=30,
                        help="Recent videos to sample for channel median (default: 30)")
    parser.add_argument("--exclude_terms", nargs="+", default=None,
                        help="Optional: drop videos whose title contains any of these substrings.")
    parser.add_argument("--skip_transcripts", action="store_true",
                        help="Skip transcript fetching (faster, but variants will be title-only).")
    parser.add_argument("--output", type=str, default=None,
                        help="Custom output path (default: output/outliers_<timestamp>.json)")
    parser.add_argument("--workers", type=int, default=3,
                        help="Parallel workers for transcript fetching")

    args = parser.parse_args()

    if not YOUTUBE_API_KEY:
        print("ERROR: YOUTUBE_API_KEY not set in .env")
        print(f"       Edit: {os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')}")
        print("       or:   ~/.config/outliers/.env (recommended if installed as a plugin)")
        print()
        print("  To get a free API key:")
        print("  1. Go to https://console.cloud.google.com/")
        print("  2. Enable 'YouTube Data API v3'")
        print("  3. Create an API key (Credentials → Create Credentials → API Key)")
        return 1

    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    estimated_quota = len(args.terms) * 100 + len(args.terms) + 200
    print(f"YouTube Outlier Detection (YouTube Data API v3)")
    print(f"  Topics: {args.terms}")
    print(f"  Min views: {args.min_views:,}")
    print(f"  Max age: {args.max_days} days")
    print(f"  Min outlier score: {args.min_score}x")
    print(f"  Limit: {args.limit}")
    if args.exclude_terms:
        print(f"  Exclude terms: {args.exclude_terms}")
    print(f"  Estimated quota: ~{estimated_quota}/10,000 units")

    published_after = (
        datetime.datetime.now(datetime.timezone.utc)
        - datetime.timedelta(days=args.max_days)
    ).strftime("%Y-%m-%dT00:00:00Z")
    print(f"  Date filter: {published_after}")
    print()

    channel_cache = {}
    all_videos = []
    print("Searching YouTube...")
    for term in args.terms:
        print(f"  Searching: {term}")
        videos = search_topic(
            youtube=youtube, query=term,
            max_results=args.results, min_views=args.min_views,
            published_after=published_after,
            channel_videos=args.channel_videos, channel_cache=channel_cache,
            exclude_terms=args.exclude_terms,
        )
        print(f"    Found {len(videos)} videos after filters")
        all_videos.extend(videos)

    seen, unique_videos = set(), []
    for v in all_videos:
        if v["video_id"] not in seen:
            seen.add(v["video_id"])
            unique_videos.append(v)

    print(f"\n{len(unique_videos)} unique videos")

    outliers = [v for v in unique_videos if v["outlier_score"] >= args.min_score]
    outliers.sort(key=lambda x: (x["outlier_score"], x.get("date", "")), reverse=True)
    outliers = outliers[:args.limit]

    if not outliers:
        print(f"\nNo videos with outlier score >= {args.min_score}. "
              f"Try --min_score 1 or a different topic.")
        return 0

    print(f"\nProcessing {len(outliers)} outliers (transcripts: "
          f"{'OFF' if args.skip_transcripts else 'ON'})...")
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(process_outlier, o, i, len(outliers), args.skip_transcripts): o
            for i, o in enumerate(outliers, 1)
        }
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"    Error: {str(e)}")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(script_dir, "output", f"outliers_{timestamp}.json")

    saved_path = save_results_json(outliers, output_path)
    print(f"\nResults saved to: {saved_path}")

    print_summary(outliers)
    print(f"\nDone! Processed {len(outliers)} outliers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
