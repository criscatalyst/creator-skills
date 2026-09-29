---
name: content-ideas
description: Full content research from the user's competitor list - scans every competitor through Instagram's official API, finds the recent organic outlier reels (sponsored ones dropped), transcribes them, keeps only those that speak to the user's audience and writes a report with the reels to learn from and how to adapt each one (angle, 3 hooks, structure, CTA keyword). Use when the user says "give me content ideas", "reel ideas", "what's working in my niche", "weekly content research", or "/content-ideas".
---

# Content ideas — from competitors to adapted ideas

One scan, one report. The user should leave with 5-8 reels to watch and, for each, what to film themselves.
Setup: this skill runs on the engine of the `competitor-report` skill (same repo). Setup steps are in this skill's `README.md`.

## 1. Scan the competitors

```bash
python3 "${CLAUDE_SKILL_DIR}/scan_competitors.py" --days 30 --min-outlier 2 --top 15 --transcribe 12 \
  --out ~/.creator-skills/research/content-ideas/data/scan-<YYYY-MM-DD>.json
```
About 5 minutes for 40 accounts. It reads `~/.creator-skills/research/competitor-list.md` (only lines starting with `@`), calls Business Discovery once per account (limit: 200 calls/hour), and keeps reels that are:
- from the last `--days` days,
- `outlier` (views / the account's median) ≥ `--min-outlier`,
- **not sponsored**: `#ad`, paid partnership, partner hashtags, or a like/view rate under a quarter of the account's usual one (boosted with budget),
- at most 3 per account. Then it transcribes the first `--transcribe`.

No competitor list yet → help the user build one (format in `README.md`), don't invent handles. If the user asks for a topic ("ideas about Claude Code"), scan anyway and filter by topic in step 3. Accounts in `accounts_failed` (not Business/Creator) → list them in the report, don't invent their data.

## 2. Load the user's context
Read `~/CLAUDE.md` and what it points to: audience (ICP), offer, content pillars, voice, hook and script rules, and any catalog of CTA keywords already in use. No `~/CLAUDE.md` → ask once who the audience is and what they sell.

## 3. Filter for the user's audience (the step that matters)
For each candidate, read transcript and caption and decide:
- **Does it speak to the user's audience?** Same pain, same kind of buyer. A reel that did millions on a topic the audience doesn't care about is a no.
- **Is the mechanism transferable?** Can the user redo it with a tool, repo, number or result that is **really theirs**? If it would take an invented number or experience, drop it.

Keep the best 5-8. The dropped ones get one line each with the reason.

## 4. Write the report
File: `~/.creator-skills/research/content-ideas/<YYYY-MM-DD>.md`, in the user's language; hooks in the language the user posts in. Structure:

1. **In short**: 3-4 lines on what's working in the niche right now (patterns across the kept reels).
2. **Reels to watch**, each with:
   - link, @account, views, outlier ×, days ago;
   - **original hook** (first line of the transcript) and **why it works** (the mechanic: promise, number, named tool, contrast, keyword);
   - **User's version**: angle for their audience · **3 hooks** in their voice (≤12 words, pain inside) · structure in 4-5 lines · the **real** tool/repo/asset of theirs to use · proposed CTA keyword (not already in their catalog, if they keep one). Verify any repo or tool you name (it exists, star count) before writing it.
3. **Dropped**: one line each: link, reason (off-audience / not transferable / sponsored).
4. **Data**: accounts scanned, failed, parameters, JSON path.

**Rules:** numbers only from the JSON. Hooks follow the user's writing rules. Don't write full scripts: when the user picks an idea, hand it to the `script-writer` skill.

## 5. Reply
In chat: the pattern in 2 lines, then one line per idea (link + best hook), then the report path. Ask which one to develop.

## Notes
- Read-only, API only: no browser in the scan, no risk to any account. The browser session (competitor-report README, part B) is only used by yt-dlp to download audio for transcripts.
- Re-run weekly: outliers from 30 days ago are already old news.
