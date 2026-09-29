# IG Competitor Research — Claude Code skill

> Part of [**creator-skills**](../../README.md). Install as a plugin: `/plugin install ig-competitor-research@creator-skills` (manual install below).

Weekly Instagram competitor research, run by Claude through a real Chrome window on your Mac. You hand it a list of competitor accounts (and optional hashtags); Claude scrolls every reels grid, ranks each account's reels by views, downloads the top performers, pulls the **first-3-seconds visual hook** (frames) and the **spoken hook + full script** (local Whisper transcript), and hands you a single ranked HTML report. You skim it and shortlist ~10 reels worth modeling.

It answers the only question that matters for short-form: *what's actually working in my niche right now, and why?* — with the hook, the visual, and the script in front of you, ranked best→worst.

> ⚠️ **Read the [Safety](#safety--read-this-first) section before your first run.** This skill drives a logged-in Instagram session. Use a throwaway account, not your main one.

## How it works

1. You start Claude Code from a folder with a `competitor-list.md` (accounts + hashtags + settings) and say *"research my competitors"*.
2. Claude opens one Chrome tab (via the Claude in Chrome extension) and scrolls each account's `/reels/` grid, collecting the top-N reel URLs **by view count** (not just the latest posts).
3. It visits each reel to pull caption / likes / comments, building a ranked pool — all written to disk as it goes, so a long run is never lost.
4. For the top reels by views, it downloads each one with `yt-dlp` (using your Chrome cookies), extracts the first-3s **frames** with `ffmpeg`, and transcribes the audio with local **Whisper** (the spoken hook + full script).
5. It renders a dark, editorial **HTML report** ranking every reel best→worst: views / likes / comments + engagement rates, the visual hook (3 frames), the spoken hook, an expandable full script, a topic + CTA tag, a one-line "why it worked", and a winning-patterns summary across the whole pool.
6. You open the HTML, skim, and shortlist the ~10 reels you want to adapt.

## Install

### 1. Dependencies (one-time)

- The **[Claude in Chrome](https://claude.ai/chrome)** extension, installed and connected. The skill drives a real Chrome window through it.
- [Homebrew](https://brew.sh), then the local toolchain for enrichment:

```bash
brew install yt-dlp ffmpeg openai-whisper
```

- **Google Chrome, logged into the Instagram account you'll scrape with** (see [Safety](#safety--read-this-first) — use a dummy account).

### 2. Install the skill

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/criscatalyst/creator-skills.git ~/creator-skills
ln -s ~/creator-skills/skills/ig-competitor-research ~/.claude/skills/ig-competitor-research
chmod +x ~/.claude/skills/ig-competitor-research/enrich-reel.sh
```

### 3. Create your competitor list

Make a `research/` folder somewhere (e.g. `~/research`) with a `competitor-list.md` inside:

```markdown
## Accounts
@competitor_one
@competitor_two
@competitor_three

## Hashtags
#youraniche
#anotherone

## Workflow settings
- reelsPerAccount: 4     # top N reels per account, by views
- scroll: true           # scroll the grid to reach older high-view reels
- scrollRounds: 3        # 3 ≈ 30-40 reels/account; more = deeper, slower
- enrichTopN: 40         # download + transcribe the top N of the whole pool
- reportTopN: 40         # how many ranked reels the HTML shows
- whisperModel: base     # 'base' handles AI jargon far better than 'tiny'
```

### 4. Run it

Start a Claude Code session **from that folder** and say:

> research my competitors

Claude picks up the `ig-competitor-research` skill and runs the full pipeline. You can also point it at accounts inline — *"research @x @y @z"* — which overrides the file for that run.

**Keep the Chrome tab visible while it runs** — Instagram won't load reels behind a backgrounded or covered window.

## How Claude runs it (for the agent)

The full operating manual is in `SKILL.md` — Claude reads it automatically. The shape of a run:

- **One Chrome tab, serial.** Instagram soft-blocks parallel sessions, so everything runs against a single tab, one step at a time.
- **Every phase persists to disk, then returns a summary.** A long run can exceed a single agent's budget; writing each phase's output to `research/` (URL pool → metadata chunks → merged pool) means nothing is held only in memory, and a failed phase is re-runnable on its own.
- **Cheap first, expensive last.** It collects metadata for the whole pool (fast, no downloads), then only downloads + transcribes the top `enrichTopN` by views — never the whole pool.
- **Verify, then retry the tail.** After the parallel download/transcribe pass, it checks every top reel has both frames and a transcript and retries any misses one at a time before writing the report.
- **The HTML is the deliverable; the markdown is the source of truth.** The body is strictly view-ranked, no editorial reordering.

## Output

```
research/
  Competitor-Research_YYYY-MM-DD.html   ← the deliverable (open this)
  Competitor-Research_YYYY-MM-DD.md     ← source of truth
  enrich/<shortcode>/
    frame_0s.jpg frame_1s.jpg frame_2s.jpg   visual hook
    hook.txt          first spoken line
    transcript.txt    full script
```

## Safety — read this first

This skill scrapes Instagram by driving a **real, logged-in Chrome session**. Treat it accordingly:

- **Strongly recommended: give the skill access to Instagram through a dummy / throwaway Instagram account — not your main one.** Claude mimics human scrolling and paces itself, so problems are unlikely, but you never know — and a ban on a burner account costs nothing, while a ban on your main account is catastrophic.
- **Don't abuse it.** It's using a real Instagram account to scrape, so keep runs to roughly **once a week**. Don't loop it, don't run huge lists back-to-back, and don't run it alongside other Instagram activity (posting, DMing) on the same account.
- **Stop on any challenge.** If Instagram shows a CAPTCHA or an "unusual activity" prompt, stop the run — don't push through it.
- Everything after the scrape (download, frames, transcript, report) runs **locally** on your Mac. Nothing is uploaded; no third-party API is involved.

## Cost

Zero. The scrape uses your own browser session; the download/frames/transcript run locally via `yt-dlp` / `ffmpeg` / Whisper. No API key, no service.

## Stack

- **Claude in Chrome** — drives the logged-in Instagram session (the only reliable way to read the reels grid; `yt-dlp`'s IG listing extractors are unreliable)
- `yt-dlp` — downloads each top reel for enrichment (via your Chrome cookies)
- `ffmpeg` — first-3s frame extraction
- `openai-whisper` — local speech-to-text for the spoken hook + script
- `render-html.py` — zero-dependency Python that renders the report

— Cris
