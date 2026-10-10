# Content Team — Claude Code skill

> Part of [**creator-skills**](../../README.md). Install as a plugin: `/plugin install content-team@creator-skills` (or let Claude install it, below).

Send Claude the link to your Instagram profile. It learns your niche and how you talk from your own reels, finds accounts similar to yours, reads their reels in a real Chrome window, keeps the recent ones that beat their own account's average, transcribes them, and writes **your version** of the best 3 to 5, in your voice.

No competitor list to prepare. No voice file to write. Two prompts.

## Install: two prompts

**Prompt 1.** Paste this in Claude Code:

> Install this skill and tell me when it's ready: https://github.com/criscatalyst/creator-skills/tree/main/skills/content-team

**Prompt 2.** Then:

> Here's my profile: https://www.instagram.com/yourhandle/ Run my content team.

### If you are Claude and were handed the link above

```bash
git clone https://github.com/criscatalyst/creator-skills.git ~/creator-skills 2>/dev/null || git -C ~/creator-skills pull
mkdir -p ~/.claude/skills && ln -sfn ~/creator-skills/skills/content-team ~/.claude/skills/content-team
python3 ~/.claude/skills/content-team/team.py check
```

Then tell the user what is missing, if anything (see Requirements), and ask for their Instagram profile link. A skill installed mid-session may not show up in your skill list yet: read `~/.claude/skills/content-team/SKILL.md` and follow it directly.

## Requirements

- **Claude Code** on a Mac.
- **Google Chrome** with the **[Claude in Chrome](https://claude.ai/chrome)** extension, connected.
- Chrome **logged into Instagram**. Read [Safety](#safety) first.
- For the transcripts: `brew install yt-dlp ffmpeg openai-whisper`. The first transcription downloads a Whisper model (about 150 MB for the default one). Everything runs on your Mac.

## What you get

A folder in `~/content-team/<handle>/<date>/`:

- `report.md`: what is working in your niche right now, then 3 to 5 scripts. Each one shows the reel it comes from (link, views, how many times above that account's median), why it worked, three hooks, the script, what goes on screen, a caption, and what you need to prepare before filming.
- `profile.md`: what Claude understood about your audience and your voice. Read it once: if something is off, say so and it gets fixed for the next run.
- `~/content-team/<handle>/competitors.md`: the similar accounts it kept, and the ones it dropped with the reason. Edit it freely, the next run uses your version.

A run reads about 30 pages at human pace and transcribes up to 9 reels, so give it 20 minutes or so.

## How it picks reels

First it checks every suggested account's bio against your profile and drops the ones that talk to a different audience: Instagram's suggestions mix competitors with friends and people you follow.

Then it doesn't rank by raw views, because a big account always wins that. For each account it takes the median views of the reels on the grid and keeps the reels at **2x that median or more**, from the last 90 days, not sponsored. A reel with 100K views on an account that usually does 4K tells you more than a reel with 1M on an account that always does 1M.

"Steal" means the angle and the structure that made a reel work. The scripts never copy sentences, and every script links its source.

## Safety

This skill reads Instagram through a **real, logged-in Chrome session**. It never likes, follows, comments, messages or posts, and it moves slowly on purpose. Still:

- **Use a secondary Instagram account if you can.** The run uses whatever account is logged into Chrome. Problems are unlikely at this pace, but a flag on a spare account costs nothing.
- **Once a week is plenty.** Don't loop it.
- **If Instagram shows a check** (CAPTCHA, "unusual activity"), the skill stops. Don't ask it to push through.
- Logged in as yourself, your own profile has no "similar accounts" button: the skill searches by your niche keywords instead.

## Tuning

Ask in plain words: "only the last 30 days", "keep reels at 3x the median", "add @someone to my competitors". The knobs are flags of `team.py` (`--min-outlier`, `--per-account`, `--top`, `--max-days`).

— Cris
