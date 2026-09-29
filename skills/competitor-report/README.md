# Competitor Report — Claude Code skill

> Part of [**creator-skills**](../../README.md). Install as a plugin: `/plugin install competitor-report@creator-skills` (manual install below).

Send Claude an Instagram profile. Get back who they are, what they talk about, which reels actually worked (outliers against their own median, with sponsored ones flagged), who their audience is, what they sell, and what you can take for your page. Built on data from Instagram's official API, plus transcripts of their best reels.

This folder also contains `ig_browser.py`, the secondary-account browser used for transcripts and for accounts the API can't see. The [content-ideas](../content-ideas/) skill runs on the same engine.

## What you get

A markdown report in `~/.creator-skills/research/competitor-reports/` with 7 sections: who they are, themes, what worked (table of outliers with hooks), audience vs yours, offer and funnel, cadence, ideas for you. Plus an 8-12 line summary in chat. About 2 minutes per profile.

## Setup

Four parts. **A** is required. **B** and **C** add transcripts and personal accounts. **D** makes the "compared to you" parts useful.

Everything lives in one folder:
```bash
mkdir -p ~/.creator-skills/research && touch ~/.creator-skills/.env && chmod 600 ~/.creator-skills/.env
```
(Want it elsewhere? Set `CREATOR_SKILLS_HOME` to another folder.)

### A. Instagram API token (required, free, ~20 minutes, once)

The skill reads other accounts through Instagram's **Business Discovery** API. It's official and free. You're not scraping, so no IP blocks and no risk to any account. You need:
- your Instagram account set as **Professional** (Business or Creator),
- linked to a **Facebook Page** (Instagram app → Settings → Accounts Center, or the Page's settings → Linked accounts).

1. **Create a Meta app.** Go to [developers.facebook.com/apps](https://developers.facebook.com/apps) → *Create app* → pick the use case for **managing messages and content on Instagram**. Leave the app in **Development** mode: as its admin you can use it without App Review.
2. **Check the permissions.** In the app: *Use cases* → Instagram → *Customize* → *API setup with Facebook login* → *Permissions and features*. These five must be there, "Ready for testing": `instagram_basic`, `instagram_manage_insights`, `pages_read_engagement`, `pages_show_list`, `business_management`. Add any that's missing.
3. **Generate a token.** Open the [Graph API Explorer](https://developers.facebook.com/tools/explorer/) → *Meta App*: your app → *User or Page*: get a user token → add the five permissions → **Generate Access Token**. In the Facebook popup, select **your Page and your Instagram account**.
4. **Extend it.** Open the [Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/), paste the token → *Debug* → **Extend Access Token** (it asks for your Facebook password). Copy the new, longer token.
5. **Get the Page token, which doesn't expire.** Back in the Explorer, paste the extended token into the *Access Token* field and run:
   ```
   GET me/accounts?fields=name,access_token,instagram_business_account
   ```
   From the Page linked to your Instagram, copy `access_token` (that's the Page token) and `instagram_business_account.id`.
6. **Save both** in `~/.creator-skills/.env`:
   ```
   IG_GRAPH_TOKEN=<the Page access_token>
   IG_GRAPH_USER_ID=<the instagram_business_account id>
   ```
7. **Test:**
   ```bash
   set -a; source ~/.creator-skills/.env; set +a
   curl -s "https://graph.facebook.com/v23.0/$IG_GRAPH_USER_ID?fields=business_discovery.username(garyvee)%7Bfollowers_count%7D&access_token=$IG_GRAPH_TOKEN"
   ```
   You should see `followers_count`.

**Renewal, every 90 days.** The Page token never expires, but Meta cuts **data access** after 90 days (the Debugger shows the date as "Data access expires"). When the API stops returning data, repeat steps 3-6. Put a reminder in your calendar a week before that date.

Not included: hashtag search. It needs a feature ("Instagram Public Content Access") that Meta only unlocks after App Review.

### B. Secondary-account browser (optional, for transcripts and personal accounts)

Downloading reels for transcripts, and reading accounts that aren't Business/Creator, needs a logged-in Instagram session. Use a **secondary account, never your real one**. The script reads pages like a person would, with pauses, and never likes, follows or comments.

1. Install Google Chrome and Playwright: `pip3 install --user playwright`. The script drives your installed Chrome, so there's no need for `playwright install`.
2. Protect your real account. Add this line to `~/.creator-skills/.env`, and the script will refuse to run if that account is ever logged in:
   ```
   IG_MAIN_ACCOUNT=<your real handle, without @>
   ```
3. Log in once with the secondary account:
   ```bash
   python3 ~/.claude/skills/competitor-report/ig_browser.py login
   ```
   A separate Chrome window opens (its own profile in `~/.social-browser/`, your everyday Chrome isn't touched). Log in, and it closes by itself once the session is saved. In the EU, Instagram may show a "free with ads / subscribe" consent screen: run `ig_browser.py open`, choose, close the window.
4. Test: `python3 ~/.claude/skills/competitor-report/ig_browser.py profile garyvee --n 6 --headless`.

(Installed as a plugin? Replace `~/.claude/skills/competitor-report` with the plugin's folder, or simply ask Claude to "log in the Instagram browser": it knows the path.)

Moving the session to another machine: close the script on both, then copy `~/.social-browser/` over (for example with `rsync`). No new login needed.

### C. Transcription tools (optional, with B)

```bash
brew install yt-dlp ffmpeg openai-whisper
```
The skill exports the secondary-account session for yt-dlp by itself (`~/.social-browser/cookies.txt`, readable only by you). Without a session, Instagram answers yt-dlp with "login required".

### D. Your context (recommended)

The report compares their audience with **yours** and adapts ideas to **your** page. For that, Claude needs your audience, offer and voice in `~/CLAUDE.md`. The [anti-slop-interview](../anti-slop-interview/) skill builds it in 30 minutes.

## Install

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/criscatalyst/creator-skills.git ~/creator-skills
ln -s ~/creator-skills/skills/competitor-report ~/.claude/skills/competitor-report
```
Or as a plugin: `/plugin install competitor-report@creator-skills`.

## Use

> analyze this competitor: https://www.instagram.com/nateherkai/

## Limits
- Personal accounts (not Business/Creator) go through the browser: views and likes, but no captions or dates, and pinned reels inflate the outliers. The report says so.
- API views include paid reach. Boosted posts are flagged, not counted as organic wins.
- Business Discovery: 200 calls per hour. One profile is 1-2 calls.

— Cris
