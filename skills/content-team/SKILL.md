---
name: content-team
description: From an Instagram profile link to reel scripts in the user's voice. Reads the user's profile to learn their niche and how they talk, finds similar accounts, reads their reels in the browser (Claude in Chrome), keeps the recent reels that beat their own account's average, transcribes them, and writes the user's version of the best ones. Use when the user sends their Instagram profile and asks for content research, reel ideas, scripts from competitors, "what should I post", "steal my competitors' reels", "run my content team", or "/content-team".
---

# Content team: from your profile to scripts in your voice

The user gives one thing: the link to their Instagram profile. They get 3-5 reel scripts, each built on a reel that recently beat its own account's average in their niche, written the way they talk.

No competitor list to prepare and no voice file to write. Both come from the profile.

## Before starting

1. **Local tools.** `python3 "${CLAUDE_SKILL_DIR}/team.py" check`. If it prints `MISSING`, show the user the install lines it printed and wait for a yes before installing anything.
2. **Browser.** This skill drives Chrome through the Claude in Chrome extension. Load the tools in one call (`ToolSearch`: `select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__javascript_tool,mcp__claude-in-chrome__computer`), call `tabs_context_mcp` with `createIfEmpty: true`, then open one new tab and keep its id. Extension not connected: stop and ask the user to connect it (https://claude.ai/chrome).
3. **Instagram session.** Open `https://www.instagram.com/`. Logged out: ask the user to log in themselves in that window (never type a password). Tell them once, in one line, that a secondary account is the safe choice because the run uses whatever account is logged in. Don't ask again.
4. **Run folder.** `RUN=~/content-team/<handle>/<YYYY-MM-DD>`, with `grids/` and `meta/` inside.

## Rules for the browser

- **Read only.** Never like, follow, comment, message, post or change a setting.
- **One tab, one page at a time**, 5 to 10 seconds between pages. At most 12 account pages and 12 reel pages per run, and one run a week per Instagram account.
- **Stop on any wall.** Login page, CAPTCHA, "unusual activity", "try again later": stop, tell the user what appeared, keep what is already on disk. Don't push through.
- **The tab must be visible.** Instagram doesn't load a grid in a hidden tab. If the first grid comes back with fewer than 3 tiles, ask the user to bring the tab to the front and retry once.
- **Write as you go.** Every page's result goes to a file in `RUN` right away, so a run that stops halfway is not lost.

The snippets below go in `javascript_tool` as they are. Each returns a JSON string: write it to the file unchanged.

```js
// PROFILE: name, bio, link, follower count as the page shows them
JSON.stringify({ header: document.querySelector('header')?.innerText ?? null, summary: document.querySelector('meta[property="og:description"]')?.content ?? null })

// GRID: every reel tile on a /reels/ page (run after scrolling)
JSON.stringify([...document.querySelectorAll('a[href*="/reel/"]')].map(a => ({ href: a.getAttribute('href'), text: a.innerText.trim(), svgs: a.querySelectorAll('svg[aria-label]').length })))

// HANDLES: profile links on the page (run before and after opening a panel, the new ones are the result)
JSON.stringify([...new Set([...document.querySelectorAll('a[href^="/"]')].map(a => (a.getAttribute('href').match(/^\/([A-Za-z0-9._]+)\/$/) || [])[1]).filter(h => h && !['explore', 'reels', 'direct', 'accounts', 'stories'].includes(h)))])

// SIMILAR: opens the "similar accounts" strip on someone's profile (the icon button next to Message)
(() => { const b = [...document.querySelectorAll('header [role=button], header button')].filter(b => !b.innerText.trim() && b.querySelector('svg[aria-label]')); const t = b[b.length - 1]; if (!t) return 'none'; t.click(); return t.querySelector('svg').getAttribute('aria-label'); })()

// REEL: date, caption and counts of the reel page you are on. Replace CODE with the reel's shortcode.
(code => { let m = null; const walk = o => { if (m || !o || typeof o !== 'object') return; if (o.code === code && 'media_type' in o) { m = o; return; } for (const k in o) walk(o[k]); }; for (const s of document.querySelectorAll('script[type="application/json"]')) { try { walk(JSON.parse(s.textContent)); } catch (e) {} } return JSON.stringify(m ? { code, user: m.user?.username ?? null, likes: m.like_count ?? null, comments: m.comment_count ?? null, taken_at: m.taken_at ?? null, caption: m.caption?.text ?? null, paid: !!m.is_paid_partnership } : { code, error: 'not_found' }); })('CODE')
```

View counts on the tiles are abbreviated in the account's language ("12.3K", "6,8 Mln"). Don't convert them yourself: `team.py` does.

## 1. Learn the user from their profile

1. Open the profile. Run `PROFILE`. Note who they are, what the bio promises, the link, the follower count.
2. Open `/<handle>/reels/`, wait 6 seconds, scroll down 3 times (2 to 4 seconds apart), run `GRID`, write the result to `RUN/grids/<handle>.json`.
3. Pick 3 of their reels: the 2 with the most views that aren't pinned (a pinned tile has `svgs: 2`) and the most recent one. Open each, run `REEL`, write `RUN/meta/<CODE>.json`.
4. Transcribe those 3, in the background while you go on:
   `python3 "${CLAUDE_SKILL_DIR}/team.py" enrich "$RUN" --into me --urls <url> <url> <url>`
5. If `~/CLAUDE.md` exists and describes the user's audience, offer or voice, read it. Where it disagrees with what you inferred, it wins.
6. Write `RUN/profile.md`:
   - who they talk to and what they sell (bio, link, how their captions close);
   - the topics they keep coming back to;
   - **how they talk**: sentence length, first or second person, the words they repeat, how their hooks open, how their calls to action are worded. Quote 5 to 8 real lines from the transcripts. This file is the voice the scripts are written in.

## 2. Find similar accounts

If `~/content-team/<handle>/competitors.md` exists, use it and skip to step 3 (the user may have edited it). Otherwise build a queue of handles:

- **A. Similar accounts.** On the user's profile run `HANDLES`, then `SIMILAR`, wait 4 seconds, run `HANDLES` again. The handles that appeared are Instagram's own suggestions. They mix real competitors with friends and people the user follows, which is why step 3 checks each one.
- **B. Search.** If `SIMILAR` returns `none` (you are logged in as the user, so it is their own profile) or A gave fewer than 5: click the search icon, type one niche keyword from `profile.md`, wait for the results, run `HANDLES`. Up to 3 keywords.

Never add a handle you didn't see on a page.

## 3. Read their reels, only from accounts in the same niche

Take the queue one account at a time, and stop when 8 accounts have passed the check or after 12 account pages. Accounts that come from an existing `competitors.md` skip the check: the user chose them.

1. Open `/<account>/reels/` and wait 6 seconds. Run `PROFILE`: the bio is on this same page.
2. **Niche check, before anything else.** Compare the bio with `RUN/profile.md`. Keep the account if it talks to the same kind of person or about the same topic as the user. A bigger account, a different format or a different style doesn't matter. Drop it if the audience is another one (a friend who posts lifestyle, a brand, a different trade). When the bio doesn't settle it, keep it: step 4 judges the single reels.
3. Kept: scroll 3 times, run `GRID`, write `RUN/grids/<account>.json`. Dropped: write nothing and move on.
4. **After the first account that clearly fits**, open its profile once, run `HANDLES`, `SIMILAR`, `HANDLES`, and put the new handles at the front of the queue. An account in the niche gets better suggestions than the user's own profile does.

Then write `~/content-team/<handle>/competitors.md`: kept accounts as `@handle` at the start of a line with a few words on why, dropped ones as `> @handle` with the reason. Lines that start with `>` are skipped on the next run. Tell the user they can edit the file.

5. Rank: `python3 "${CLAUDE_SKILL_DIR}/team.py" rank "$RUN" --me <handle>`. For every account it computes the median views of the reels on the grid and keeps the reels at 2x that median or more, at most 2 per account, 10 in total. Accounts with too few reels are skipped and listed.
6. Open the candidates from the top, at most 8. On each run `REEL` and write `RUN/meta/<CODE>.json`.
7. Transcribe: `python3 "${CLAUDE_SKILL_DIR}/team.py" enrich "$RUN" --n 6`. It drops what is older than 90 days or sponsored, then for each reel it keeps saves `RUN/reels/<CODE>/transcript.txt` and the frames of the first three seconds. About a minute per reel: run it in the background.

## 4. Keep what fits the user's audience

An account in the niche still posts reels that are off topic. For each transcribed reel, read the transcript, the caption and `frame_0s.jpg`, then decide:

- **Does it speak to the user's audience?** Same pain, same kind of buyer. A reel with millions of views on a topic their audience doesn't care about is a no.
- **Can the user redo it with something that is really theirs?** A tool they use, a number they have, a story they lived. If it would take an invented result, drop it.

Keep the best 3 to 5. Every dropped reel gets one line with the reason.

## 5. Write the scripts

Read `references/script-guide.md` and follow it. One script per kept reel, in the language the user posts in, in the voice of `RUN/profile.md`.

What "legally steal" means here: take the **angle and the structure** that made the reel work, never its sentences. Every script links the reel it comes from.

## 6. Report

Write `RUN/report.md` in the user's language:

1. **In short**: 3 lines on what is working in their niche right now, across the kept reels.
2. **Scripts**, one block each: the source reel (link, @account, views, multiple of the account's median, days ago), its original hook and why it worked, then the user's script in the format of the guide, and what they need to prepare before filming.
3. **Dropped**: link and reason, one line each.
4. **Data**: accounts read, accounts dropped at the niche check (with the reason), accounts skipped for too few reels, the path of `candidates.json`.

In chat: the pattern in two lines, then one line per script (the hook and the source reel), then the path of the report. Ask which one they want to refine.

## Notes

- Numbers come only from the files in `RUN`. A reel without a transcript (download failed, no speech) is judged on caption and frames, and the report says so.
- No usable account at all (private profiles, no reels): say it, and ask the user for 5 handles they consider competitors.
- Re-run weekly at most. A reel that beat the average 3 months ago is old news.
