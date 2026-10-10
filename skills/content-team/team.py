#!/usr/bin/env python3
"""Helper for the content-team skill: the parts that should not be left to guesswork.

  python3 team.py check                          # are yt-dlp, ffmpeg and whisper installed?
  python3 team.py rank RUN [--me HANDLE]         # grids/*.json -> medians, outliers, candidates.json
  python3 team.py enrich RUN [--n 6]             # download + transcribe the top candidates (recent, not sponsored)
  python3 team.py enrich RUN --urls URL [URL..] --into me   # the user's own reels (voice sample)

RUN is the run folder, e.g. ~/content-team/<handle>/<YYYY-MM-DD>. The browser part of the skill
writes one file per account in RUN/grids/<handle>.json: the raw tiles of the profile's reels grid,
[{"href": "/handle/reel/CODE/", "text": "12,3K", "svgs": 1}, ...], and one file per visited reel in
RUN/meta/<CODE>.json: {"code", "user", "likes", "comments", "taken_at", "caption", "paid"}.
Standard library only.
"""
import argparse
import json
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TOOLS = {"yt-dlp": "brew install yt-dlp", "ffmpeg": "brew install ffmpeg", "whisper": "brew install openai-whisper"}
# Instagram abbreviates view counts in the language of the account: 12.3K, 6,8 Mln, 12,3 mila, 1,2 Mio...
THOUSAND = {"k", "mila", "mil", "tsd", "tys", "тыс"}
MILLION = {"m", "mln", "mio", "mi", "mill", "млн"}
BILLION = {"b", "mld", "mrd", "bn"}


def parse_views(text):
    """'6,8 Mln' -> 6800000, '17K' -> 17000, '1.456' -> 1456, '' -> None."""
    m = re.search(r"(\d[\d.,   ]*)\s*([^\W\d_]+)?", (text or "").strip())
    if not m:
        return None
    num, suffix = m.group(1).strip().replace(" ", "").replace(" ", "").replace(" ", ""), (m.group(2) or "").lower().rstrip(".")
    mult = 1e3 if suffix in THOUSAND else 1e6 if suffix in MILLION else 1e9 if suffix in BILLION else None
    if mult:  # abbreviated: the separator is a decimal mark
        return int(float(num.replace(",", ".")) * mult)
    digits = re.sub(r"[.,]", "", num)  # plain count: separators group thousands
    return int(digits) if digits else None


def code_of(href):
    m = re.search(r"/(?:reel|reels|p)/([A-Za-z0-9_-]+)", href or "")
    return m.group(1) if m else None


def load_grid(path):
    """Tiles of one account -> [{code, url, views, pinned}], grid order, no duplicates."""
    rows, seen = [], set()
    for t in json.loads(Path(path).read_text()):
        code = code_of(t.get("href") or t.get("url"))
        if not code or code in seen:
            continue
        seen.add(code)
        svgs = t.get("svgs", 1)
        rows.append({"code": code, "url": f"https://www.instagram.com/reel/{code}/",
                     "views": parse_views(t.get("text")) if "views" not in t else t["views"],
                     # a normal tile carries one icon (the view count), a pinned one carries two
                     "pinned": (len(svgs) if isinstance(svgs, list) else int(svgs or 0)) >= 2})
    return rows


def cmd_check(args):
    missing = [f"{t}: {TOOLS[t]}" for t in TOOLS if not shutil.which(t)]
    if missing:
        print("MISSING\n" + "\n".join(missing))
        sys.exit(10)
    print("OK", subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True).stdout.strip())


def cmd_rank(args):
    run = Path(args.run).expanduser()
    me = (args.me or "").lstrip("@").lower()
    accounts, candidates = [], []
    for path in sorted((run / "grids").glob("*.json")):
        handle = path.stem
        rows = load_grid(path)
        views = [r["views"] for r in rows if r["views"] and not r["pinned"]]
        median = statistics.median(views) if views else None
        acc = {"handle": handle, "reels": len(rows), "with_views": len(views), "median_views": median,
               "usable": bool(median) and len(views) >= args.min_reels}
        accounts.append(acc)
        if handle.lower() == me or not acc["usable"]:
            continue
        picked = sorted((dict(r, handle=handle, outlier=round(r["views"] / median, 1)) for r in rows
                         if r["views"] and not r["pinned"] and r["views"] / median >= args.min_outlier),
                        key=lambda r: -r["outlier"])[: args.per_account]
        candidates += picked
    # the same multiple means more on an account with real reach: break ties on raw views
    candidates.sort(key=lambda r: (-r["outlier"], -r["views"]))
    candidates = candidates[: args.top]
    out = {"me": me or None, "params": {"min_outlier": args.min_outlier, "per_account": args.per_account,
                                        "top": args.top, "min_reels": args.min_reels},
           "accounts": accounts, "candidates": candidates}
    (run / "candidates.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    for a in accounts:
        note = "" if a["usable"] else "  <- skipped: too few reels with a view count"
        print(f"@{a['handle']}: {a['reels']} reels, median {a['median_views']}{note}")
    print(f"\n{len(candidates)} candidates -> {run / 'candidates.json'}")
    for c in candidates:
        print(f"  {c['outlier']}x  {c['views']:>9} views  @{c['handle']}  {c['url']}")


def run_quiet(cmd):
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def enrich_one(url, out, model):
    code = code_of(url) or "reel"
    dest = out / code
    if (dest / "transcript.txt").exists():
        return {"code": code, "skipped": True}
    dest.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        video = Path(tmp) / "video.mp4"
        base = ["yt-dlp", "--no-warnings", "--quiet", "-f", "worst[ext=mp4]/worst", "-o", str(video), url]
        # public reels download without a login on a current yt-dlp; the Chrome session is the fallback
        if not (run_quiet(base) and video.exists()) and not (
                run_quiet(base[:1] + ["--cookies-from-browser", "chrome"] + base[1:]) and video.exists()):
            return {"code": code, "error": "download_failed"}
        frames = all(run_quiet(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-ss", str(s), "-i", str(video),
                                "-frames:v", "1", "-q:v", "3", str(dest / f"frame_{s}s.jpg")]) for s in (0, 1, 2))
        ok = run_quiet(["whisper", str(video), "--model", model, "--output_format", "txt", "--output_dir", tmp,
                        "--fp16", "False", "--verbose", "False"])
        text = (Path(tmp) / "video.txt").read_text().strip() if ok and (Path(tmp) / "video.txt").exists() else ""
    if text:
        (dest / "transcript.txt").write_text(text + "\n")
    return {"code": code, "frames": frames, "transcript": bool(text)}


SPONSORED = re.compile(r"#(ad|adv|sponsored|partner|gifted|paidpartnership)\b|paid partnership", re.I)


def keep(run, cand, max_days):
    """Why a candidate is dropped (None = keep), from what the browser read on its page."""
    path = run / "meta" / f"{cand['code']}.json"
    if not path.exists():
        return None  # not visited: nothing to judge it on
    meta = json.loads(path.read_text())
    if meta.get("taken_at") and (time.time() - meta["taken_at"]) / 86400 > max_days:
        return f"older than {max_days} days"
    if meta.get("paid") or SPONSORED.search(meta.get("caption") or ""):
        return "sponsored"
    return None


def cmd_enrich(args):
    run = Path(args.run).expanduser()
    if args.urls:
        urls = args.urls
    else:
        urls = []
        for c in json.loads((run / "candidates.json").read_text())["candidates"]:
            why = keep(run, c, args.max_days)
            if why:
                print(json.dumps({"code": c["code"], "dropped": why}), flush=True)
            elif len(urls) < args.n:
                urls.append(c["url"])
    out = run / args.into
    for url in urls:  # one at a time: parallel downloads get rate-limited
        print(json.dumps(enrich_one(url, out, args.model)), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    r = sub.add_parser("rank")
    r.add_argument("run")
    r.add_argument("--me", help="the user's own handle: ranked for its median, never a candidate")
    r.add_argument("--min-outlier", type=float, default=2.0)
    r.add_argument("--per-account", type=int, default=2)
    r.add_argument("--top", type=int, default=10)
    r.add_argument("--min-reels", type=int, default=6)
    e = sub.add_parser("enrich")
    e.add_argument("run")
    e.add_argument("--n", type=int, default=6)
    e.add_argument("--urls", nargs="+")
    e.add_argument("--into", default="reels", help="subfolder of RUN (use 'me' for the user's own reels)")
    e.add_argument("--model", default="base")
    e.add_argument("--max-days", type=int, default=90)
    args = ap.parse_args()
    {"check": cmd_check, "rank": cmd_rank, "enrich": cmd_enrich}[args.cmd](args)


if __name__ == "__main__":
    main()
