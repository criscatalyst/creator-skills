#!/bin/bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <url> [model=small] [language=auto]" >&2
  exit 1
fi

URL="$1"
MODEL="${2:-small}"
LANG="${3:-}"

TMPDIR=$(mktemp -d -t transcribe.XXXXXX)
trap 'rm -rf "$TMPDIR"' EXIT

echo "[1/2] Downloading audio from: $URL" >&2
yt-dlp \
  --no-playlist \
  --extract-audio \
  --audio-format mp3 \
  --audio-quality 0 \
  -o "$TMPDIR/audio.%(ext)s" \
  "$URL" >&2

AUDIO=$(find "$TMPDIR" -name 'audio.*' | head -n1)
if [ -z "$AUDIO" ] || [ ! -f "$AUDIO" ]; then
  echo "ERROR: yt-dlp did not produce an audio file." >&2
  exit 2
fi

echo "[2/2] Transcribing with whisper ($MODEL${LANG:+, lang=$LANG})..." >&2

LANG_ARGS=()
[ -n "$LANG" ] && LANG_ARGS=(--language "$LANG")

whisper "$AUDIO" \
  --model "$MODEL" \
  --output_dir "$TMPDIR" \
  --output_format txt \
  --fp16 False \
  ${LANG_ARGS[@]+"${LANG_ARGS[@]}"} >&2

TXT=$(find "$TMPDIR" -name '*.txt' | head -n1)
if [ -z "$TXT" ] || [ ! -f "$TXT" ]; then
  echo "ERROR: whisper produced no transcript." >&2
  exit 3
fi

echo "" >&2
echo "=== TRANSCRIPT ===" >&2
cat "$TXT"
