---
name: competitor-report
description: Data-backed report on an Instagram competitor from their profile link or handle - who they are, what they talk about, which posts worked best (outliers vs their own median, sponsored posts flagged), who they talk to (their ICP) and what they sell, plus what the user can take for their own page. Use when the user sends an Instagram profile and asks to analyze a competitor, "who is this", "what do they sell", "who do they talk to", "competitor report", or "/competitor-report".
---

# Competitor report

The user sends an Instagram profile, you return a report built on data, not on impressions.
Setup (token, secondary account, tools) is in this skill's `README.md`. If a step fails for a missing setup piece, point the user to the matching README section instead of guessing.

## 1. Collect the data

```bash
python3 "${CLAUDE_SKILL_DIR}/profile_data.py" "<profile link or handle>" --n 60 --transcribe-top 8 \
  --out ~/.creator-skills/research/competitor-reports/data/<handle>-<YYYY-MM-DD>.json
```
(`~/.creator-skills` is the default; if the user set `CREATOR_SKILLS_HOME`, use that instead.) Takes 1-2 minutes, mostly transcription. What it does:
- **Source 1, official API** (Instagram Business Discovery): bio, website, followers, and for each post caption, date, format, views, likes, comments. Works for Business/Creator accounts, which is almost every competitor.
- **Source 2, fallback** for personal accounts: a Chrome logged in with the user's secondary account (`ig_browser.py profile`). Plays/likes/comments only, **no captions or dates**: say so in the report and run `python3 "${CLAUDE_SKILL_DIR}/ig_browser.py" post <url>` on the top 3-5 reels to get their captions.
- **Transcripts** of the 8 strongest outliers (yt-dlp with the secondary-account session + whisper). Many creators write empty captions like "Comment X", so *what they talk about* mostly comes from here. Whisper `base` mangles names ("Clawed" = Claude): fix them in the report.
- **Pre-analysis**: median reel views, `outlier` = views / median, top 10 outliers, outliers from the last 60 days, posts per week, format mix, CTAs in captions, "Comment X" keywords, hashtags, website title and description.

Typical errors: `IG_GRAPH_TOKEN missing` → README, part A. `Instagram is asking for a manual step` → `python3 "${CLAUDE_SKILL_DIR}/ig_browser.py" open`, the user clears the screen by hand. API returns no data though the token is valid → the 90-day data access expired, README part A, "Renewal".

## 2. Load the user's context
Read `~/CLAUDE.md` and what it points to for the user's audience (ICP), offer and content pillars. That's what "who do they talk to compared to you" and "what you can take" are measured against. No `~/CLAUDE.md` → ask once who the user's audience is.

## 3. Write the report
File: `~/.creator-skills/research/competitor-reports/<handle>-<YYYY-MM-DD>.md`, in the user's language. Sections:

1. **Who they are**: name, handle, followers, post count, what the bio says, website. 2-4 lines.
2. **What they talk about**: 3-5 recurring themes, each with 1-2 example posts (links). From captions and transcripts, not from hashtags alone.
3. **What worked**: table of the best 5-8 outliers: link, views, outlier ×, days ago, hook (first line of the transcript or caption), why you think it worked. Separate **recent (≤60 days)** from old hits. Mark pinned reels as pinned.
4. **Who they talk to (ICP)**: their audience, with evidence (bio, caption, transcript lines). Compare with the user's ICP: same audience, overlapping, or different?
5. **What they sell**: offer and funnel ("Comment X" → DM → lead magnet → product/service), what's on the website (title, description, links). Prices only if you actually see them.
6. **Cadence and formats**: posts per week, reels vs carousels, median views.
7. **What the user can take**: 3-5 concrete ideas (format, hook, CTA mechanic), adapted to the user's ICP and voice.

**Sponsored posts:** API views include paid reach. An outlier with `#ad`, "paid partnership", a partner hashtag, or a like rate far below the account's usual one may have been boosted: flag it and don't use it as proof of what works organically.

**Rules:** every number comes from the JSON. What you infer (ICP, why a reel worked) is written as an inference with its evidence. If a section lacks data, say so instead of filling it.

## 4. Reply
In chat: 8-12 lines with who they are, what they sell, who they talk to, the 3 reels to watch (links) and the 2 most useful ideas. Then the path of the full report.

## Safety
Read-only: no follows, likes, comments or DMs from the browser. The browser only ever runs on the secondary account (`IG_MAIN_ACCOUNT` blocks the real one). One profile per request is fine; for dozens in a row use the API (200 calls/hour) and leave the browser out.
