#!/usr/bin/env python3
"""Instagram via a real, logged-in Chrome (secondary account only).

Opens pages like a person would and reads the JSON the page itself downloads,
instead of calling Instagram's private API from a script (that is what gets IPs
blocked). Uses a dedicated Chrome profile, never your everyday one.

  python3 ig_browser.py login                     # one-time: log in as the secondary account
  python3 ig_browser.py open                      # visible window, for consent screens / checks by hand
  python3 ig_browser.py cookies                   # export the session for yt-dlp (--cookies ~/.social-browser/cookies.txt)
  python3 ig_browser.py profile <handle> [--n 24] # latest reels with plays/likes/comments
  python3 ig_browser.py post <url>                # a post (likes, comments, caption) + the first comments

Profile dir: ~/.social-browser/chrome-profile (local, never synced: it holds the session).
Set IG_MAIN_ACCOUNT in ~/.creator-skills/.env: the tool refuses to run if that account is logged in.
"""
import argparse
import json
import os
import re
import random
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

PROFILE_DIR = Path.home() / ".social-browser" / "chrome-profile"
COOKIES_FILE = Path.home() / ".social-browser" / "cookies.txt"
CONFIG_DIR = Path(os.environ.get("CREATOR_SKILLS_HOME", Path.home() / ".creator-skills"))


def _env(key):
    if os.environ.get(key):
        return os.environ[key]
    path = CONFIG_DIR / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip().strip('"')
    return None


# Accounts this tool must never run on (your real account). Comma-separated, without @.
MAIN_ACCOUNTS = {a.strip().lstrip("@").lower() for a in (_env("IG_MAIN_ACCOUNT") or "").split(",") if a.strip()}
MAX_SCROLLS = 15


def pause(lo=2.0, hi=5.0):
    time.sleep(random.uniform(lo, hi))


def launch(p, headless):
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    ctx = p.chromium.launch_persistent_context(
        str(PROFILE_DIR), channel="chrome", headless=headless,
        viewport={"width": 1280, "height": 900}, locale="it-IT",
    )
    return ctx, (ctx.pages[0] if ctx.pages else ctx.new_page())


def logged_in_username(page, payloads):
    """Username of the session in this profile ("?" if logged in but not found), None if logged out.
    Read from what the page already loaded: no extra API call."""
    uid = next((c["value"] for c in page.context.cookies("https://www.instagram.com")
                if c["name"] == "ds_user_id"), None)
    if not uid:
        return None
    for payload in payloads:
        for d in walk(payload):
            if str(d.get("pk") or d.get("id") or d.get("pk_id") or "") == uid and d.get("username"):
                return d["username"]
    html = page.content()
    for m in re.finditer(r'"username":"([A-Za-z0-9._]+)"', html):
        if uid in html[max(0, m.start() - 400): m.end() + 400]:
            return m.group(1)
    return "?"


def guard(page, payloads):
    user = logged_in_username(page, payloads)
    if not user:
        sys.exit("Not logged in. Run: python3 ig_browser.py login")
    if "consent" in page.url or "challenge" in page.url:
        sys.exit(f"Instagram is asking for a manual step ({page.url}). Run: python3 ig_browser.py open")
    if not MAIN_ACCOUNTS:
        print("Warning: IG_MAIN_ACCOUNT is not set, so nothing stops this from running on your real account.",
              file=sys.stderr)
    if user.lower() in MAIN_ACCOUNTS:
        sys.exit(f"Logged in as @{user}: this tool must only run on a secondary account. Log out and log in with the secondary one.")
    return user


def walk(obj):
    """Yield every dict nested anywhere in a JSON value."""
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v)


def capture_json(page, sink):
    def on_response(resp):
        url = resp.url
        if "instagram.com" not in url or not any(k in url for k in ("/graphql", "/api/v1/")):
            return
        try:
            text = resp.text()
        except Exception:
            return
        for line in text.splitlines():  # streamed GraphQL = one JSON document per line
            try:
                sink.append(json.loads(line))
            except ValueError:
                pass
    page.on("response", on_response)


def page_json(page):
    """JSON the server embedded in the HTML (post pages ship their data this way, not via XHR)."""
    docs = []
    for text in page.evaluate("""() => [...document.querySelectorAll('script[type="application/json"]')].map(s => s.textContent)"""):
        try:
            docs.append(json.loads(text))
        except ValueError:
            pass
    return docs


def media_rows(payloads):
    """Media nodes in the order the page received them (grid order: pinned first, then newest)."""
    rows = {}
    for payload in payloads:
        for d in walk(payload):
            code = d.get("code")
            if not isinstance(code, str) or "media_type" not in d:
                continue
            cap = d.get("caption")
            row = rows.setdefault(code, {"code": code, "url": f"https://www.instagram.com/p/{code}/"})
            for key, val in (("plays", d.get("play_count") or d.get("ig_play_count") or d.get("view_count")),
                             ("likes", d.get("like_count")), ("comments", d.get("comment_count")),
                             ("taken_at", d.get("taken_at")),
                             ("caption", cap.get("text") if isinstance(cap, dict) else None),
                             ("pinned", bool(d.get("clips_tab_pinned_user_ids")) or None)):
                if val is not None:
                    row[key] = val
    return list(rows.values())


def cmd_login(args):
    with sync_playwright() as p:
        ctx, page = launch(p, headless=False)
        payloads = []
        capture_json(page, payloads)
        page.goto("https://www.instagram.com/accounts/login/")
        print("Log in with the SECONDARY account in the Chrome window (waiting up to 10 min)...", flush=True)
        deadline = time.time() + 600
        while time.time() < deadline:
            if any(c["name"] == "sessionid" for c in ctx.cookies("https://www.instagram.com")):
                page.goto("https://www.instagram.com/")
                pause(3, 4)
                user = logged_in_username(page, payloads)
                if user and user.lower() in MAIN_ACCOUNTS:
                    print(f"WARNING: logged in as @{user} (main account). Log out and use the secondary one.")
                else:
                    print(f"OK: session saved for @{user}")
                ctx.close()
                return
            time.sleep(3)
        ctx.close()
        sys.exit("Timed out waiting for login.")


def cmd_open(args):
    with sync_playwright() as p:
        ctx, page = launch(p, headless=False)
        page.goto("https://www.instagram.com/")
        print("Window open. Close it when done.", flush=True)
        page.wait_for_event("close", timeout=0)
        ctx.close()


def cmd_cookies(args):
    """Netscape cookie file so yt-dlp can download reels as the secondary account."""
    with sync_playwright() as p:
        ctx, page = launch(p, headless=True)
        cookies = ctx.cookies("https://www.instagram.com")
        ctx.close()
    if not any(c["name"] == "sessionid" for c in cookies):
        sys.exit("Not logged in. Run: python3 ig_browser.py login")
    lines = ["# Netscape HTTP Cookie File"]
    for c in cookies:
        lines.append("\t".join([c["domain"], "TRUE" if c["domain"].startswith(".") else "FALSE", c["path"],
                                "TRUE" if c["secure"] else "FALSE", str(int(max(c["expires"], 0))), c["name"], c["value"]]))
    COOKIES_FILE.write_text("\n".join(lines) + "\n")
    COOKIES_FILE.chmod(0o600)
    print(COOKIES_FILE)


def cmd_profile(args):
    with sync_playwright() as p:
        ctx, page = launch(p, args.headless)
        payloads = []
        capture_json(page, payloads)
        page.goto("https://www.instagram.com/")
        pause()
        user = guard(page, payloads)
        payloads.clear()  # drop the home feed, keep only this profile
        page.goto(f"https://www.instagram.com/{args.handle}/reels/")
        pause(4, 6)
        for _ in range(MAX_SCROLLS):
            if len(media_rows(payloads)) >= args.n:
                break
            page.mouse.wheel(0, random.randint(1500, 2500))
            pause()
        rows = media_rows(payloads)[: args.n]
        ctx.close()
    print(json.dumps({"handle": args.handle, "via": user, "count": len(rows), "reels": rows}, ensure_ascii=False, indent=2))


def cmd_post(args):
    m = re.search(r"/(?:p|reel|reels)/([A-Za-z0-9_-]+)", args.url)
    if not m:
        sys.exit("Not a post/reel URL")
    code = m.group(1)
    with sync_playwright() as p:
        ctx, page = launch(p, args.headless)
        payloads = []
        capture_json(page, payloads)
        page.goto("https://www.instagram.com/")
        pause()
        user = guard(page, payloads)
        payloads.clear()
        page.goto(f"https://www.instagram.com/p/{code}/")  # /p/ shows the comments, /reel/ hides them
        pause(5, 7)
        payloads += page_json(page)
        comments = {}
        for payload in payloads:
            for d in walk(payload):
                u = d.get("user")
                if isinstance(d.get("text"), str) and isinstance(u, dict) and d.get("created_at") and d.get("pk"):
                    comments[d["pk"]] = {"user": u.get("username"), "text": d["text"],
                                         "likes": d.get("comment_like_count"), "created_at": d["created_at"]}
        post = next((r for r in media_rows(payloads) if r["code"] == code), None)
        ctx.close()
    print(json.dumps({"via": user, "post": post,
                      "comments": sorted(comments.values(), key=lambda c: c["likes"] or 0, reverse=True)},
                     ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("login")
    sub.add_parser("open")
    sub.add_parser("cookies")
    pr = sub.add_parser("profile")
    pr.add_argument("handle")
    pr.add_argument("--n", type=int, default=24)
    pr.add_argument("--headless", action="store_true", help="may get flagged by Instagram; default is a visible window")
    po = sub.add_parser("post")
    po.add_argument("url")
    po.add_argument("--headless", action="store_true")
    args = ap.parse_args()
    {"login": cmd_login, "open": cmd_open, "cookies": cmd_cookies, "profile": cmd_profile, "post": cmd_post}[args.cmd](args)


if __name__ == "__main__":
    main()
