# Content Ideas — Claude Code skill

> Part of [**creator-skills**](../../README.md). Install as a plugin: `/plugin install competitor-report@creator-skills` and `/plugin install content-ideas@creator-skills` (manual install below).

Say "give me content ideas". Claude scans every competitor on your list, finds the reels that beat their own average in the last 30 days (sponsored ones dropped), transcribes them, keeps only the ones that speak to **your** audience, and writes a report: which reels to watch, why they worked, and your version of each one with 3 hooks, a structure and a CTA keyword.

## What you get

A markdown report in `~/.creator-skills/research/content-ideas/` plus a short summary in chat. About 5 minutes of scanning for 40 competitors, then the writing.

Example of what a scan surfaces: across 41 AI-niche accounts, "5 secret commands for ChatGPT" listicles at 52-108× the account's median, "paid tool vs free GitHub repo" at 29-47×, "AI did my annoying chore end to end" at 38× with 1.1M views.

## Setup

**This skill uses the engine of [competitor-report](../competitor-report/).** Do its setup first:
- **Part A (required):** the Instagram API token in `~/.creator-skills/.env`.
- **Parts B + C (recommended):** secondary-account browser + yt-dlp/whisper, for transcripts. Without them the scan still works, but reels are judged from captions only, and many captions are just "Comment X".
- **Part D (recommended):** your audience and voice in `~/CLAUDE.md`. The audience filter is what turns "viral reels" into "ideas for you".

Then create your competitor list:

```bash
cp ~/creator-skills/skills/content-ideas/competitor-list.example.md ~/.creator-skills/research/competitor-list.md
```

and edit it. Rules:
- **One `@handle` per line, at the start of the line.** Anything after it on the line is ignored, so you can keep notes there.
- Lines that don't start with `@` are ignored: use `> @handle` to park an account without deleting it.
- Pick accounts that post regularly in your niche and talk to a similar audience. 20-50 is a good size. Follower count predicts little: check that their recent reels actually get views.
- Only Business/Creator accounts can be read by the API. The others end up in "failed" in the report.

## Install

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/criscatalyst/creator-skills.git ~/creator-skills
ln -s ~/creator-skills/skills/competitor-report ~/.claude/skills/competitor-report
ln -s ~/creator-skills/skills/content-ideas ~/.claude/skills/content-ideas
```
Both folders are needed: `content-ideas` imports its engine from `competitor-report`.

## Use

> give me content ideas for my reels

> what's working in my niche this week? focus on Claude Code

Then pick an idea and hand it to [script-writer](../script-writer/).

## Tuning

`scan_competitors.py` flags, if you want to ask Claude for a different cut:
- `--days 30`: how recent (14 for "this week's trends", 60 for a wider net)
- `--min-outlier 2`: how far above the account's median a reel must be
- `--top 15` / `--transcribe 12`: how many candidates, how many transcripts

— Cris
