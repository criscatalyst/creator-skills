# Video Breakdown — Claude Code skill

> Part of [**creator-skills**](../../README.md). Install as a plugin: `/plugin install video-breakdown@creator-skills` (manual install below).

Break any video down into its **visuals** and its **audio**, locally on your Mac. Paste a URL, and Claude reverse-engineers it shot by shot — what's on screen at every second **and** what's being said — using `yt-dlp` + `ffmpeg` + OpenAI Whisper. Free, no API key, nothing uploaded.

Works on Instagram reels, TikTok, YouTube / YT Shorts, X/Twitter, Vimeo — anything `yt-dlp` supports.

## How it works

1. You paste a video URL into Claude Code: *"break down the visuals of this reel"*.
2. Claude downloads the full video with `yt-dlp`.
3. Splits the audio track out with `ffmpeg`.
4. Samples frames at your chosen rate, with the **timestamp burned into each frame**, and tiles them into contact-sheet grids.
5. Transcribes the audio with local Whisper into a **timestamped** transcript.
6. Reads the frames + transcript and hands you a shot-by-shot breakdown: hook, pacing, text overlays, b-roll, structure, CTA.

## Install (5 minutes)

### 1. Dependencies (one-time)

You need [Homebrew](https://brew.sh). Then:

```bash
brew install yt-dlp ffmpeg openai-whisper
```

### 2. Install the skill

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/criscatalyst/creator-skills.git ~/creator-skills
ln -s ~/creator-skills/skills/video-breakdown ~/.claude/skills/video-breakdown
chmod +x ~/.claude/skills/video-breakdown/breakdown.sh
```

### 3. Try it

Start a new Claude Code session and paste:

> break down the visuals of this reel: https://www.instagram.com/reel/...

Claude picks up the `video-breakdown` skill and runs it. The first run also downloads the Whisper model weights (~500MB for the default `small` model), then they're cached.

## Run it yourself (optional)

You don't have to — Claude drives it for you — but the script is a normal CLI:

```bash
~/.claude/skills/video-breakdown/breakdown.sh "<URL>" [fps] [whisper_model] [language] [outdir]
```

Example — a fast-cut reel, 2 frames/sec:

```bash
~/.claude/skills/video-breakdown/breakdown.sh "https://www.tiktok.com/@x/video/123" 2
```

You get a folder with:

```
video.mp4          full video
audio.mp3          extracted audio track
transcript.txt     plain transcript
transcript.srt     timestamped transcript
frames/            sampled frames, timestamp burned top-left
sheets/            contact-sheet grids of all frames
```

## Options

| Option | Default | When to change it |
|---|---|---|
| `fps` (frames/sec) | `1` | `0.5` for long videos, `2` for fast-cut reels |
| `whisper_model` | `small` | `medium` for accents/noise, `tiny`/`base` for speed, `large-v3` for best quality |
| `language` | auto | Pass `en` / `it` / … if auto-detect guesses wrong on short clips |

## Cost

Zero. Everything runs locally on your machine. No API.

## Common issues

- **Private reel / login-walled** → `yt-dlp` can't reach it. Ask Claude to retry with your browser cookies (`--cookies-from-browser safari`).
- **Silent / music-only video** → no transcript (expected); the visual breakdown still works.
- **Wrong language detected** → tell Claude the language and re-run.
- **Too many frames** on a long video → lower the `fps` (e.g. `0.5`).

## Stack

- `yt-dlp` — pulls video from almost any site
- `ffmpeg` — audio split, frame sampling, contact sheets, timestamp overlay
- `openai-whisper` — OpenAI's speech-to-text, run locally

— Cris
