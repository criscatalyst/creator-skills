---
name: transcribe
description: Transcribe any video URL (Instagram reel, TikTok, YouTube / YT Shorts, Twitter/X, Facebook, Vimeo — anything yt-dlp supports) using local OpenAI Whisper. Trigger when the user pastes a video URL and asks to "transcribe", "get the script", "what does he say", or wants spoken content as text.
---

# Transcribe

Transcribe any video URL using `yt-dlp` + local `whisper`.

## When to use

- User pastes a URL (IG reel, TikTok, YouTube, YT Short, Twitter/X video, Vimeo, etc.) and asks for the transcript / script
- User wants to study a competitor's hook, pacing, structure
- User wants spoken content from a long-form YouTube video as text

## How to invoke

```bash
"${CLAUDE_SKILL_DIR}/transcribe.sh" "<URL>" [model] [language]
```

- `model` — whisper model. Default `small`. Use `medium` for noisier audio / accents, `tiny` for speed, `large-v3` for highest quality (slow).
- `language` — ISO code (`it`, `en`, `es`, …). Default: auto-detect. Pass it explicitly if auto-detect mis-fires (common on very short clips).

The script prints the transcript to stdout. Audio is downloaded to a tempdir and deleted on exit.

### Long-form videos

For YouTube videos longer than ~10 min, prefer `tiny` or `base` model unless the user explicitly wants high accuracy — `small`+ on a 30-min video can take several minutes on CPU. Warn the user about wait time before starting.

If the YouTube video has official captions, mention the user could pull those instead via `yt-dlp --write-auto-subs --skip-download` for instant results — but only suggest, don't switch automatically (whisper is more accurate than auto-generated captions).

## Output handling

Present the transcript inside a clear block. After showing it, offer follow-ups based on what the user is likely doing:
- Reel/short → offer hook breakdown, structure beats, CTA extraction
- Long-form → offer summary, key timestamps, quote pull-outs

Don't do these automatically. Ask first.

## Failure modes

- **Private / login-walled content** → yt-dlp fails. Tell the user; offer to retry with `--cookies-from-browser safari` (or chrome).
- **No audio track** → whisper returns empty. Mention it; the video is likely silent / music-only.
- **Wrong language detected** → re-run with explicit `language` arg.
- **Geo-blocked YouTube video** → suggest a VPN or different source.

## Notes

- Tools used: `yt-dlp` + `ffmpeg` + `whisper` (Homebrew, all installed).
- First run with a given model downloads weights (~500MB `small`, ~1.5GB `medium`, ~3GB `large`). Cached in `~/.cache/whisper/`.
