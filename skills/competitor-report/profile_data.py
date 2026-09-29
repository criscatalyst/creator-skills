#!/usr/bin/env python3
"""Collect + pre-analyse an Instagram competitor profile for the competitor-report skill.

  python3 profile_data.py <handle|profile url> [--n 60] [--transcribe-top 3] [--out file.json]

Source 1: Business Discovery API (IG_GRAPH_TOKEN / IG_GRAPH_USER_ID, see README): bio, website,
          followers, and per post caption, date, format, views, likes, comments.
Source 2 (fallback, non-business accounts): ig_browser.py profile, a Chrome logged in with a
          secondary account (plays/likes/comments only, no captions).
Optional: transcripts of the top outlier reels (yt-dlp with the secondary-account session + whisper).

Config: ~/.creator-skills/.env (or $CREATOR_SKILLS_HOME/.env), environment variables win.
"""
import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG_DIR = Path(os.environ.get("CREATOR_SKILLS_HOME", Path.home() / ".creator-skills"))
RESEARCH_DIR = CONFIG_DIR / "research"
BROWSER = HERE / "ig_browser.py"
COOKIES = Path.home() / ".social-browser" / "cookies.txt"
GRAPH = "https://graph.facebook.com/v23.0"
MEDIA_FIELDS = "id,caption,timestamp,media_type,media_product_type,like_count,comments_count,view_count,permalink"
ENV_PATH = os.pathsep.join([str(Path.home() / ".local/bin"), "/opt/homebrew/bin", "/usr/local/bin", os.environ.get("PATH", "")])


def env(key):
    if os.environ.get(key):
        return os.environ[key]
    path = CONFIG_DIR / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip().strip('"')
    return None


def handle_of(arg):
    m = re.search(r"instagram\.com/([A-Za-z0-9._]+)", arg)
    return (m.group(1) if m else arg).lstrip("@").strip("/")


def graph_get(url):
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return json.load(e)


def business_discovery(handle, n):
    token, uid = env("IG_GRAPH_TOKEN"), env("IG_GRAPH_USER_ID")
    if not token:
        return None, f"IG_GRAPH_TOKEN missing (set it in {CONFIG_DIR / '.env'}, see README)"
    profile, media, after = None, [], None
    while len(media) < n:
        page = f"media.limit({min(50, n - len(media))})" + (f".after({after})" if after else "")
        fields = f"business_discovery.username({handle}){{username,name,biography,website,followers_count,follows_count,media_count,{page}{{{MEDIA_FIELDS}}}}}"
        d = graph_get(f"{GRAPH}/{uid}?" + urllib.parse.urlencode({"fields": fields, "access_token": token}))
        if "error" in d:
            if profile is None:
                return None, d["error"].get("message")
            break  # keep the pages already fetched
        bd = d["business_discovery"]
        profile = profile or {k: v for k, v in bd.items() if k != "media"}
        media += bd.get("media", {}).get("data", [])
        after = bd.get("media", {}).get("paging", {}).get("cursors", {}).get("after")
        if not after:
            break
    profile["media"] = media
    return profile, None


def browser_fallback(handle, n):
    out = subprocess.run([sys.executable, str(BROWSER), "profile", handle, "--n", str(n), "--headless"],
                         capture_output=True, text=True, timeout=300)
    if out.returncode != 0:
        return None, out.stderr.strip()[-300:]
    d = json.loads(out.stdout)
    media = [{"permalink": r["url"], "media_product_type": "REELS", "view_count": r.get("plays"),
              "like_count": r.get("likes"), "comments_count": r.get("comments"), "pinned": r.get("pinned")}
             for r in d["reels"]]
    return {"username": handle, "media": media}, None


def website_info(url):
    if not url:
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read(400_000).decode("utf-8", "ignore")
            final = r.geturl()
        title = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
        desc = re.search(r'<meta[^>]+(?:name|property)=["\'](?:og:)?description["\'][^>]+content=["\'](.*?)["\']', html, re.I)
        links = sorted(set(re.findall(r'href=["\'](https?://[^"\']+)["\']', html)))[:40]
        return {"final_url": final, "title": title and title.group(1).strip()[:200],
                "description": desc and desc.group(1).strip()[:400], "outbound_links": links}
    except Exception as e:
        return {"error": str(e)[:200]}


CTA_PATTERNS = {
    "comment_keyword": r"(?i:comment\w*)\s+[\"“'‘]?([A-Z][A-Z0-9]{2,})\b",  # keyword itself must be CAPS
    "link_in_bio": r"link in (?:my )?bio",
    "dm": r"\bDM\b|\bdm me\b|send me a (?:dm|message)",
    "free": r"\bfree\b",
    "price": r"[$€£]\s?\d",
}


def analyse(profile):
    media = profile["media"]
    now = datetime.now(timezone.utc)
    for m in media:
        ts = m.get("timestamp")
        m["days_ago"] = (now - datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z")).days if ts else None
    reels = [m for m in media if m.get("media_product_type") == "REELS" and m.get("view_count")]
    med_views = statistics.median(m["view_count"] for m in reels) if reels else None
    likes = [m["like_count"] for m in media if m.get("like_count") is not None]
    med_likes = statistics.median(likes) if likes else None
    for m in media:
        if med_views and m.get("view_count") and m in reels:
            m["outlier"] = round(m["view_count"] / med_views, 2)
        elif med_likes and m.get("like_count"):
            m["outlier_likes"] = round(m["like_count"] / med_likes, 2)
    dated = [m["days_ago"] for m in media if m.get("days_ago") is not None]
    span_weeks = max((max(dated) - min(dated)) / 7, 1) if dated else None
    captions = [m.get("caption") or "" for m in media]
    ctas = {k: sum(1 for c in captions if re.search(p, c, 0 if k == "comment_keyword" else re.I))
            for k, p in CTA_PATTERNS.items()}
    keywords = Counter(k.upper() for c in captions for k in re.findall(CTA_PATTERNS["comment_keyword"], c))
    hashtags = Counter(h.lower() for c in captions for h in re.findall(r"#(\w+)", c))
    return {
        "posts_analysed": len(media),
        "format_mix": dict(Counter(m.get("media_product_type") or m.get("media_type") for m in media)),
        "posts_per_week": round(len(dated) / span_weeks, 1) if span_weeks else None,
        "median_reel_views": med_views,
        "median_likes": med_likes,
        "top_reels_by_outlier": sorted(reels, key=lambda m: m["view_count"] / med_views, reverse=True)[:10] if reels else [],
        "top_non_reels_by_likes": sorted([m for m in media if m not in reels and m.get("like_count")],
                                         key=lambda m: m["like_count"], reverse=True)[:5],
        "recent_outliers_60d": [m for m in reels if m.get("days_ago") is not None and m["days_ago"] <= 60 and m.get("outlier", 0) >= 2],
        "cta_counts": ctas,
        "comment_keywords": keywords.most_common(10),
        "top_hashtags": hashtags.most_common(15),
    }


def transcribe(url, model):
    if not COOKIES.exists():
        subprocess.run([sys.executable, str(BROWSER), "cookies"], capture_output=True, timeout=120)
    envv = dict(os.environ, PATH=ENV_PATH)
    with tempfile.TemporaryDirectory() as tmp:
        dl = subprocess.run(["yt-dlp", "-q", "--no-warnings", "--cookies", str(COOKIES), "-x", "--audio-format", "mp3",
                             "-o", f"{tmp}/a.%(ext)s", url], capture_output=True, text=True, env=envv, timeout=300)
        audio = next(Path(tmp).glob("a.*"), None)
        if not audio:
            return {"error": (dl.stderr or "download failed").strip()[-200:]}
        subprocess.run(["whisper", str(audio), "--model", model, "--output_dir", tmp, "--output_format", "txt", "--fp16", "False"],
                       capture_output=True, text=True, env=envv, timeout=900)
        txt = next(Path(tmp).glob("*.txt"), None)
        return {"text": txt.read_text().strip()} if txt else {"error": "whisper produced no transcript"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("profile")
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--transcribe-top", type=int, default=0)
    ap.add_argument("--whisper-model", default="base")
    ap.add_argument("--out")
    a = ap.parse_args()
    handle = handle_of(a.profile)

    profile, err = business_discovery(handle, a.n)
    source = "business_discovery_api"
    if profile is None:
        print(f"Business Discovery failed ({err}); falling back to the browser.", file=sys.stderr)
        profile, err2 = browser_fallback(handle, min(a.n, 36))
        source = "browser_secondary_account"
        if profile is None:
            sys.exit(f"Both sources failed. API: {err} | browser: {err2}")

    result = {"handle": handle, "source": source, "collected_at": datetime.now().isoformat(timespec="minutes"),
              "profile": {k: v for k, v in profile.items() if k != "media"},
              "website": website_info(profile.get("website")),
              "analysis": analyse(profile), "media": profile["media"]}
    for m in result["analysis"]["top_reels_by_outlier"][: a.transcribe_top]:
        print(f"Transcribing {m['permalink']} ...", file=sys.stderr)
        m["transcript"] = transcribe(m["permalink"], a.whisper_model)

    text = json.dumps(result, ensure_ascii=False, indent=2)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text)
        print(a.out)
    else:
        print(text)


if __name__ == "__main__":
    main()
