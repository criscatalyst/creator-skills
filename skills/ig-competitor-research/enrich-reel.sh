#!/bin/bash
# =============================================================================
# enrich-reel.sh — enrich ONE Instagram reel with visual + spoken hook.
# Downloads the reel (yt-dlp, Chrome cookies), extracts the first-3s hook frames
# (ffmpeg @ 0/1/2s), and transcribes the spoken hook (Whisper).
#
# Usage: bash enrich-reel.sh <reel-url> <out-dir> [whisper-model]
#   <reel-url>       full https://www.instagram.com/reel/<code>/ URL
#   <out-dir>        where to write results (created if missing)
#   [whisper-model]  tiny (default) | base | small
#
# Output in <out-dir>/<code>/:
#   frame_0s.jpg frame_1s.jpg frame_2s.jpg   visual hook (first 3 seconds)
#   transcript.txt                            full spoken transcript
#   hook.txt                                  first spoken line (the spoken hook)
#
# Requires a Chrome logged into Instagram — cookies are pulled automatically.
# Prints one JSON line on stdout for the orchestrator to parse.
# =============================================================================
set -euo pipefail

URL="${1:-}"
OUT_ROOT="${2:-}"
MODEL="${3:-tiny}"

if [ -z "$URL" ] || [ -z "$OUT_ROOT" ]; then
  echo '{"error":"usage: enrich-reel.sh <reel-url> <out-dir> [model]"}'
  exit 1
fi

CODE=$(echo "$URL" | grep -oE '/(reel|p)/[A-Za-z0-9_-]+' | grep -oE '[A-Za-z0-9_-]+$' | head -1)
[ -z "$CODE" ] && CODE="reel_$$"
OUT="$OUT_ROOT/$CODE"
mkdir -p "$OUT"

# Skip if already enriched
if [ -f "$OUT/frame_0s.jpg" ] && [ -f "$OUT/transcript.txt" ]; then
  echo "{\"code\":\"$CODE\",\"skipped\":true,\"dir\":\"$OUT\"}"
  exit 0
fi

VIDEO="$OUT/video.mp4"

# 1. Download (worst quality is enough for frames + audio). Chrome cookies = IG auth.
if ! python3 -m yt_dlp --cookies-from-browser chrome --no-warnings --quiet \
      -f "worst[ext=mp4]/worst" -o "$VIDEO" "$URL" >/dev/null 2>&1; then
  echo "{\"code\":\"$CODE\",\"error\":\"download_failed\"}"
  exit 0
fi
[ ! -f "$VIDEO" ] && { echo "{\"code\":\"$CODE\",\"error\":\"no_video\"}"; exit 0; }

# 2. Visual hook — frames at 0s, 1s, 2s.
HAS_FRAMES=true
for SEC in 0 1 2; do
  ffmpeg -nostdin -y -loglevel error -ss "$SEC" -i "$VIDEO" \
    -frames:v 1 -q:v 3 "$OUT/frame_${SEC}s.jpg" 2>/dev/null || HAS_FRAMES=false
done

# 3. Spoken hook — transcribe with Whisper (feeds mp4 directly).
HAS_TRANSCRIPT=false
if whisper "$VIDEO" --model "$MODEL" --language en --output_format txt \
     --output_dir "$OUT" --fp16 False --verbose False >/dev/null 2>&1; then
  # Whisper names the txt after the input file → video.txt
  if [ -f "$OUT/video.txt" ]; then
    mv "$OUT/video.txt" "$OUT/transcript.txt"
    # First non-empty line = the spoken hook
    grep -m1 -E '.{5,}' "$OUT/transcript.txt" | sed 's/^ *//' > "$OUT/hook.txt" || true
    HAS_TRANSCRIPT=true
  fi
fi

# 4. Drop the video, keep frames + transcript (saves disk across many reels).
rm -f "$VIDEO"

echo "{\"code\":\"$CODE\",\"dir\":\"$OUT\",\"frames\":$HAS_FRAMES,\"transcript\":$HAS_TRANSCRIPT}"
