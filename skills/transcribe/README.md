# Transcribe — Claude Code skill

> Part of [**creator-skills**](../../README.md). Install as a plugin: `/plugin install transcribe@creator-skills` (manual install below).

Transcribe any video URL (Instagram reels, TikTok, YouTube, YT Shorts, Twitter/X, Vimeo, and anything yt-dlp supports) using OpenAI Whisper running locally on your Mac. Free, no API key, no uploads.

## How it works

1. You paste a video URL into Claude Code and ask "transcribe this".
2. Claude downloads only the audio with `yt-dlp`.
3. Pipes it into local `whisper` for speech-to-text.
4. Prints the transcript right back in chat.

## Install (5 minutes)

### 1. Install dependencies (one-time)

You need [Homebrew](https://brew.sh). If you don't have it, install that first.

```bash
brew install yt-dlp ffmpeg openai-whisper
```

### 2. Install the skill

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/criscatalyst/creator-skills.git ~/creator-skills
ln -s ~/creator-skills/skills/transcribe ~/.claude/skills/transcribe
chmod +x ~/.claude/skills/transcribe/transcribe.sh
```

### 3. Try it

Start a new Claude Code session and paste:

> transcribe this: https://www.instagram.com/reel/...

Claude will pick up the `transcribe` skill and run it. The first run downloads the Whisper model weights (~500MB for the default `small` model), then they're cached.

## Options

- **Model**: defaults to `small` (fast, good for short-form). Use `medium` for noisy audio or strong accents. Use `large-v3` for top-tier quality (slow).
- **Language**: auto-detected. On very short clips it sometimes guesses wrong — just tell Claude "transcribe in English" / "in Italian" and re-run.

## Cost

Zero. Everything runs locally. No API.

## Common issues

- **Private reel** → yt-dlp fails. You need to be logged in; Claude will offer to retry using your browser cookies.
- **Wrong language detected** → tell it the language and rerun.
- **Silent / music-only video** → empty transcript. Expected.

## Stack

- `yt-dlp` — pulls audio from almost any video site
- `ffmpeg` — audio conversion
- `openai-whisper` — OpenAI's speech-to-text model, run locally

— Cris
