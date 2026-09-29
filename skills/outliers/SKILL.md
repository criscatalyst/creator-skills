---
name: outliers
description: YouTube outlier detection. Given a topic, finds the highest-performing recent videos on that topic — ranked by views ÷ channel median (so a 10x outlier means the video did 10 times the channel's normal performance). Reads each video's transcript and generates 3 personalized title variants per outlier, adapted to the user's niche and voice from their ~/CLAUDE.md. Trigger when the user says "find outliers", "/outliers", "show me viral videos in <topic>", or asks what's working on YouTube right now for a topic.
---

# Outliers

Topic-based YouTube outlier detection + content-aware title variant generation.

Given a topic, the script finds the recent videos that **massively over-performed their channel's average** (5x, 10x, 20x normal views), pulls their transcripts, and helps you write 3 title variants per outlier — adapted to your niche and your voice.

The value: ranking by `views ÷ channel median` filters out big channels that always do millions and surfaces real viral patterns from smaller channels.

## When to trigger

- User says "find outliers", "outlier hunt", "/outliers"
- User pastes a topic and asks for viral examples ("what's working in fitness right now")
- User asks for content ideas based on what's performing on YouTube
- Weekly content planning sessions

## How to invoke

The script lives next to this SKILL.md. The user must pass a topic via `--terms`.

```bash
cd "${CLAUDE_SKILL_DIR}"
source venv/bin/activate 2>/dev/null || (python3 -m venv venv && source venv/bin/activate && pip install -q -r requirements.txt)

ARGS="$1"
if [ -z "$ARGS" ]; then
  echo "Pass a topic, e.g. /outliers fitness for busy parents" && exit 1
elif [[ "$ARGS" == --* ]]; then
  python outlier_detector.py $ARGS
else
  python outlier_detector.py --terms "$ARGS"
fi
```

Common usage:
- Bare topic → auto-wrapped into `--terms "<topic>"`, transcripts ON
- `--terms "X" "Y"` → multiple search terms in one run
- `--skip_transcripts` → faster, no transcripts (variants will be title-only)
- `--min_score 3` → only keep outliers above 3x baseline
- `--max_days 14` → only videos posted in the last 14 days
- `--min_views 50000` → raise the floor on absolute views
- `--exclude_terms "shorts" "news"` → drop titles containing these substrings
- `--limit 5` → top 5 only

## Steps

### 1. Run the detector

Use the bash block above. The script writes a JSON file to `${CLAUDE_SKILL_DIR}/output/`.

### 2. Read the latest output JSON

Find the newest file in `output/` and load it. Each entry contains: `title`, `channel_name`, `view_count`, `days_old`, `outlier_score`, `url`, and `transcript_excerpt` (first 8000 chars of transcript when available).

### 3. Read the user's CLAUDE.md

Read `~/CLAUDE.md` (Voice rules, Anti-slop rules, Offer & goals, About me sections) to learn the user's niche, ICP, voice, and banned words.

If `~/CLAUDE.md` doesn't exist or has no Offer & goals section, ask the user once for: niche + ICP one-liner. Don't proceed with generic variants — they have to land in the user's space.

### 4. For each outlier, write a content summary

For every outlier with a non-empty `transcript_excerpt`, write 2–3 sentences:
- What the video actually teaches: the specific concept, tool, workflow, framework, or insight.
- The concrete demo or example shown (if any).
- Why this hook earned the views (loss aversion, contrarian claim, specific number, transformation arc, etc.)

Skip this step for outliers without a transcript — flag them clearly so the user knows the variants are title-only.

### 5. Generate 3 content-aware title variants per outlier

Each variant must:
- **Reference a real concept, tool, number, or example from the transcript** — not a generic riff on the original title.
- Adapt the angle to the user's niche/ICP/offer (pulled from `~/CLAUDE.md`).
- Keep the same psychological mechanism that made the original work (pattern interrupt, contrarian claim, specific number, transformation, etc.)
- Be meaningfully different from each other (vary angle, specificity, framing).
- Stay under 100 characters.
- Match the user's voice rules from CLAUDE.md (no banned words, no AI-tells, no em dashes if banned).

Variants without transcript anchoring tend to be generic — the whole point of having transcripts on by default is to make variants land on real content.

### 6. Present results

For each outlier:

```
**#N — "Original Title" (SCOREx outlier)**
Channel | Views | Days old
URL

Content summary: [2-3 sentences on what the video actually teaches and why the hook works]

Title variants (content-aware):
1. "Variant 1"
2. "Variant 2"
3. "Variant 3"
```

If a variant is anchored on a specific transcript detail, you can briefly note it in parentheses (e.g. "(refs the Notion + Claude demo at minute 4)") to help the user verify it.

## Setup requirements

- **YouTube Data API v3 key** — free at https://console.cloud.google.com (enable YouTube Data API v3 → create API key). Free tier: 10,000 quota units/day. A single-topic run uses ~300 units.
- A `.env` with `YOUTUBE_API_KEY=...`, either in the skill folder or at `~/.config/outliers/.env` (use the latter when installed as a plugin: plugin updates replace the skill folder).

If neither exists, tell the user to copy `.env.example` to `~/.config/outliers/.env` and fill it.

## Cost / quota notes

- Single-topic run: ~300 quota units → ~30 runs/day on the free tier.
- If quota hits the daily cap, the API returns an error and the script returns empty. Wait until midnight Pacific Time (when YouTube resets) or use a different API key.

## Anti-patterns

- ❌ Don't generate generic title variants. They must reference both the user's niche AND a real detail from the video transcript.
- ❌ Don't run the script without a topic — the user must pass `--terms`.
- ❌ Don't run the script without checking `.env` first — it'll fail silently with a confusing error.
- ❌ Don't claim a video is an outlier if its `outlier_score` is < 2x. Below that, it's not really a viral signal.

## Why this skill exists

Watching only your own niche means you only see the same patterns recycled. Watching outliers — videos that beat their own channel's baseline by 5x or more — surfaces hooks that earned attention against the channel's normal performance. That's a stronger signal than absolute view count, because a channel doing 10M views every video doesn't tell you anything new about which hook worked.

Adapt the hook structure to your niche, anchor the variant on what the video actually teaches, and you've got a content idea grounded in real audience demand instead of guesses.
