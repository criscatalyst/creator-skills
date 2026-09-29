# Outliers — Claude Code skill

> Part of [**creator-skills**](../../README.md). Install as a plugin: `/plugin install outliers@creator-skills` (manual install below).

YouTube outlier detection + content-aware title variant generation.

Given a topic, finds the recent videos that **massively over-performed their channel's average** (5x, 10x, 20x normal views), reads each video's transcript, and generates 3 title variants per outlier — adapted to your niche, your ICP, and your voice from `~/CLAUDE.md`.

## What it does

1. Searches YouTube for the topic you pass in (e.g. `fitness for busy parents`, `personal finance`, `claude code`).
2. For each video found, computes **outlier score** = `video views ÷ channel median views` (sampled from the channel's last 30 uploads). A 10x outlier means the video did 10 times the channel's normal performance.
3. Filters out shorts, non-English audio, and the YouTube gaming category.
4. Pulls the transcript (first 8000 chars) for each top outlier.
5. Reads your `~/CLAUDE.md` to learn your niche, ICP, voice rules, and offer.
6. Generates 3 title variants per outlier, anchored on what the video *actually teaches* — not just a riff on the original title.

## Why outlier score, not raw views

A channel that always does 10M views doesn't tell you anything new — that's just the channel. A 1k-median channel with one video at 500k? **That's** a viral signal. Ranking by `views ÷ channel median` surfaces patterns from smaller channels you can actually learn from, instead of celebrity content you can't copy.

## Install

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/criscatalyst/creator-skills.git ~/creator-skills
ln -s ~/creator-skills/skills/outliers ~/.claude/skills/outliers
cd ~/.claude/skills/outliers
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then edit `.env` and fill in your `YOUTUBE_API_KEY`.

Installed as a plugin instead? Put the key in `~/.config/outliers/.env`: plugin updates replace the skill folder, that file survives them.

## Get a YouTube API key (free, 5 min)

1. Go to https://console.cloud.google.com
2. Create a project (or use an existing one)
3. APIs & Services → Library → search **YouTube Data API v3** → Enable
4. APIs & Services → Credentials → Create credentials → API key
5. Copy the key into `.env` as `YOUTUBE_API_KEY=...`

Free tier: **10,000 quota units / day**. A single-topic run uses ~300 units, so you can do roughly 30 hunts per day at zero cost.

## Usage

In Claude Code:

> /outliers fitness for busy parents

> /outliers personal finance for women

> /outliers claude code best skills

> /outliers --terms "investing" "stock market" --max_days 14

The skill runs the detector, reads each transcript, and presents every outlier with a content summary + 3 title variants in your voice.

### Options

- `--terms "X" "Y"` — one or more topic strings (required)
- `--min_score N` — minimum outlier multiplier to keep (default: 1.5)
- `--min_views N` — minimum absolute view count (default: 10,000)
- `--max_days N` — only videos posted in the last N days (default: 30)
- `--limit N` — keep top N outliers (default: 10)
- `--exclude_terms "X" "Y"` — drop videos whose titles contain any of these substrings
- `--skip_transcripts` — faster, no transcripts (variants will be title-only)

## Output format

For each outlier:

```
**#3 — "I Quit My $200K Job. Biggest Mistake Of My Life." (12x outlier)**
@JohnDoe | 2.4M views | 14 days old

Content summary: John walks through the moment he gave notice, the 6 months of
financial anxiety that followed, and the specific spreadsheet he wished he'd
built before quitting. The hook works because it pairs loss aversion ("biggest
mistake") with a public confession — viewers click to find out what went wrong.

Title variants (content-aware):
1. "I Quit Posting To Build A Course. Biggest Mistake Of My Life."
2. "I Sold My First Digital Product For $50k. Biggest Mistake Of My Life."
3. "The Spreadsheet I Wish I Built Before Quitting My Job"
```

The third variant pulls a specific detail from the transcript — that's the kind of variant that lands.

## Personalization via ~/CLAUDE.md

The skill reads your `~/CLAUDE.md` (specifically the Voice rules, Anti-slop rules, About me, and Offer & goals sections) to know:

- **Your niche** → so variants are in your space, not generic
- **Your ICP** → so variants speak to YOUR audience
- **Your voice rules** → so variants don't use words you've banned (e.g. no em dashes, no "actually", no AI-tells)
- **Your offer** → so variants point to what you sell, not random adjacent topics

If you haven't run [`anti-slop-interview`](../anti-slop-interview/) yet, the outliers skill will ask you for niche + ICP one-liner before generating variants. Better to run `anti-slop-interview` once — every other skill (this one included) gets sharper afterwards.

## Cost

Zero. YouTube API free tier covers ~30 single-topic runs / day. No paid services required.

## Pairs well with

- [`anti-slop-interview`](../anti-slop-interview/) — bootstrap your `~/CLAUDE.md` so outliers gets your niche right.
- [`script-writer`](../script-writer/) — once you pick a title variant, generate the full script with Hook → Build-Up → Value → Payoff → CTA.
- [`hemingway`](../hemingway/) — readability check on the script before you record.

## Stack

- `google-api-python-client` — YouTube Data API v3
- `python-dotenv` — env var loading
- `youtube-transcript-api` — transcript fetching (v1.x instance API)

— Cris
