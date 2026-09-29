#!/usr/bin/env python3
"""Scan every competitor in the list and return the recent organic outlier reels, transcribed.

  python3 scan_competitors.py [--days 30] [--min-outlier 2] [--top 15] [--transcribe 12] [--out file.json]

Per account: Business Discovery API (last --per-account posts) -> outlier = views / account median.
Keeps reels posted within --days, outlier >= --min-outlier, not flagged as paid, max 3 per account.
Used by the content-ideas skill, which does the ICP filter and the adaptation.
Needs the competitor-report skill folder next to this one (it ships in the same repo).
"""
import argparse
import json
import re
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

# Shared engine lives in the sibling competitor-report skill (same repo).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "competitor-report"))
from profile_data import RESEARCH_DIR, analyse, business_discovery, transcribe  # noqa: E402

LIST = RESEARCH_DIR / "competitor-list.md"
PAID = re.compile(r"#ad\b|paid partnership|#sponsored|#\w*partner\b", re.I)


def handles(path):
    """Active accounts only: lines starting with @ (quarantined ones start with '>')."""
    return [m.group(1) for line in Path(path).read_text().splitlines() if (m := re.match(r"@([A-Za-z0-9._]+)", line))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", default=str(LIST))
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--per-account", type=int, default=30)
    ap.add_argument("--min-outlier", type=float, default=2.0)
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--transcribe", type=int, default=12)
    ap.add_argument("--whisper-model", default="base")
    ap.add_argument("--out")
    a = ap.parse_args()

    ok, failed, candidates = [], [], []
    for i, h in enumerate(handles(a.list), 1):
        print(f"[{i}] @{h}", file=sys.stderr, flush=True)
        profile, err = business_discovery(h, a.per_account)
        if profile is None:
            failed.append({"handle": h, "error": err})
            continue
        stats = analyse(profile)
        reels = [m for m in profile["media"] if m.get("outlier")]
        rates = [m["like_count"] / m["view_count"] for m in reels if m.get("like_count") is not None]
        med_rate = statistics.median(rates) if rates else None
        ok.append({"handle": h, "followers": profile.get("followers_count"), "median_reel_views": stats["median_reel_views"],
                   "posts_per_week": stats["posts_per_week"], "reels": len(reels)})
        picked = 0
        for m in sorted(reels, key=lambda m: m["outlier"], reverse=True):
            if m["days_ago"] is None or m["days_ago"] > a.days or m["outlier"] < a.min_outlier or picked >= 3:
                continue
            paid = bool(PAID.search(m.get("caption") or "")) or (
                med_rate is not None and m.get("like_count") is not None and m["like_count"] / m["view_count"] < 0.25 * med_rate)
            if paid:
                continue
            picked += 1
            candidates.append({"handle": h, "followers": profile.get("followers_count"),
                               "account_median_views": stats["median_reel_views"], "permalink": m["permalink"],
                               "views": m["view_count"], "outlier": m["outlier"], "days_ago": m["days_ago"],
                               "likes": m.get("like_count"), "comments": m.get("comments_count"), "caption": m.get("caption") or ""})
        time.sleep(1)

    candidates.sort(key=lambda c: c["outlier"], reverse=True)
    candidates = candidates[: a.top]
    for c in candidates[: a.transcribe]:
        print(f"Transcribing @{c['handle']} {c['permalink']}", file=sys.stderr, flush=True)
        c["transcript"] = transcribe(c["permalink"], a.whisper_model)

    result = {"generated_at": datetime.now().isoformat(timespec="minutes"),
              "params": {k: v for k, v in vars(a).items() if k != "out"},
              "accounts_ok": ok, "accounts_failed": failed, "candidates": candidates}
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text)
        print(a.out)
    else:
        print(text)


if __name__ == "__main__":
    main()
