#!/bin/bash
# video-breakdown — download a video, split audio/video, sample timestamped frames
# + contact sheets for visual analysis, and transcribe the audio with local Whisper.
set -euo pipefail

# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------
if [ $# -lt 1 ]; then
  cat >&2 <<'USAGE'
Usage: breakdown.sh <url> [fps] [whisper_model] [language] [outdir]

  url            Video URL (Instagram reel, TikTok, YouTube/Short, X, Vimeo, …)
  fps            Frames sampled per second.   Default 1   (use 0.5 for long videos, 2 for fast cuts)
  whisper_model  tiny | base | small | medium | large-v3.  Default small
  language       ISO code (en, it, es, …).    Default auto-detect
  outdir         Output folder.               Default ./video-breakdown-<timestamp>

Produces in <outdir>/:
  video.mp4          full downloaded video
  audio.mp3          extracted audio track
  transcript.txt     plain transcript
  transcript.srt     timestamped transcript (for aligning visuals to speech)
  frames/            sampled frames, timestamp burned top-left (frame_0001.jpg …)
  sheets/            contact-sheet grids of all frames (sheet_001.png …)
USAGE
  exit 1
fi

URL="$1"
FPS="${2:-1}"
MODEL="${3:-small}"
LANG="${4:-}"
OUTDIR="${5:-./video-breakdown-$(date +%Y%m%d-%H%M%S)}"

# ---------------------------------------------------------------------------
# Preflight: dependencies
# ---------------------------------------------------------------------------
MISSING=()
for cmd in yt-dlp ffmpeg whisper; do
  command -v "$cmd" >/dev/null 2>&1 || MISSING+=("$cmd")
done
if [ ${#MISSING[@]} -gt 0 ]; then
  echo "ERROR: missing dependencies: ${MISSING[*]}" >&2
  echo "Install with:  brew install yt-dlp ffmpeg openai-whisper" >&2
  exit 10
fi

# Pick a usable font for the burned-in timestamp (macOS + Linux fallbacks).
FONT=""
for f in \
  /System/Library/Fonts/Supplemental/Arial.ttf \
  /System/Library/Fonts/Supplemental/Courier\ New.ttf \
  /Library/Fonts/Arial.ttf \
  /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf \
  /usr/share/fonts/TTF/DejaVuSans.ttf ; do
  [ -f "$f" ] && FONT="$f" && break
done

mkdir -p "$OUTDIR/frames" "$OUTDIR/sheets"

# ---------------------------------------------------------------------------
# 1. Download the full video
# ---------------------------------------------------------------------------
echo "[1/5] Downloading video: $URL" >&2
yt-dlp \
  --no-playlist \
  -f "bv*+ba/b" \
  --merge-output-format mp4 \
  -o "$OUTDIR/video.%(ext)s" \
  "$URL" >&2

VIDEO=$(find "$OUTDIR" -maxdepth 1 -name 'video.*' | head -n1)
if [ -z "$VIDEO" ] || [ ! -f "$VIDEO" ]; then
  echo "ERROR: yt-dlp did not produce a video file." >&2
  echo "  - Private / login-walled? Re-run with: --cookies-from-browser safari (or chrome)" >&2
  echo "  - YouTube SABR / 403 / \"missing a URL\" warning? yt-dlp is stale: brew upgrade yt-dlp (or yt-dlp -U), then retry." >&2
  echo "  - See $OUTDIR/.ffmpeg.log for ffmpeg-side errors." >&2
  exit 2
fi
# Normalize to .mp4 path for downstream steps
if [ "$VIDEO" != "$OUTDIR/video.mp4" ]; then
  mv "$VIDEO" "$OUTDIR/video.mp4" 2>/dev/null || true
fi
VIDEO="$OUTDIR/video.mp4"

# ---------------------------------------------------------------------------
# 2. Split out the audio track
# ---------------------------------------------------------------------------
echo "[2/5] Extracting audio track -> audio.mp3" >&2
if ffmpeg -hide_banner -loglevel error -y -i "$VIDEO" -vn -acodec libmp3lame -q:a 0 "$OUTDIR/audio.mp3" 2>>"$OUTDIR/.ffmpeg.log"; then
  HAS_AUDIO=1
else
  echo "  (no audio track found — likely a silent / music-only clip)" >&2
  HAS_AUDIO=0
fi

# ---------------------------------------------------------------------------
# 3. Sample timestamped frames
# ---------------------------------------------------------------------------
echo "[3/5] Sampling frames at ${FPS} fps (timestamp burned top-left)" >&2
TS_DRAW=""
if [ -n "$FONT" ]; then
  TS_DRAW=",drawtext=fontfile='${FONT}':text='%{pts\:hms}':x=20:y=20:fontsize=40:fontcolor=yellow:box=1:boxcolor=black@0.6:boxborderw=10"
else
  echo "  (no TTF font found — frames will not have a burned-in timestamp; frame N ≈ N/${FPS}s)" >&2
fi
ffmpeg -hide_banner -loglevel error -y -i "$VIDEO" \
  -vf "fps=${FPS}${TS_DRAW}" \
  -q:v 3 \
  "$OUTDIR/frames/frame_%04d.jpg" 2>>"$OUTDIR/.ffmpeg.log"
NFRAMES=$(find "$OUTDIR/frames" -name 'frame_*.jpg' | wc -l | tr -d ' ')
echo "  -> $NFRAMES frames" >&2

# ---------------------------------------------------------------------------
# 4. Build contact-sheet grids (efficient visual overview)
# ---------------------------------------------------------------------------
echo "[4/5] Building contact sheets (5x6 grid per page)" >&2
ffmpeg -hide_banner -loglevel error -y -i "$VIDEO" \
  -vf "fps=${FPS},scale=360:-1:force_original_aspect_ratio=decrease${TS_DRAW},tile=5x6:padding=8:margin=8:color=white" \
  "$OUTDIR/sheets/sheet_%03d.png" 2>>"$OUTDIR/.ffmpeg.log"
NSHEETS=$(find "$OUTDIR/sheets" -name 'sheet_*.png' | wc -l | tr -d ' ')
echo "  -> $NSHEETS sheet(s)" >&2

# ---------------------------------------------------------------------------
# 5. Transcribe audio with Whisper (timestamped)
# ---------------------------------------------------------------------------
if [ "$HAS_AUDIO" -eq 1 ]; then
  echo "[5/5] Transcribing audio with whisper ($MODEL${LANG:+, lang=$LANG})…" >&2
  LANG_ARGS=()
  [ -n "$LANG" ] && LANG_ARGS=(--language "$LANG")
  whisper "$OUTDIR/audio.mp3" \
    --model "$MODEL" \
    --output_dir "$OUTDIR" \
    --output_format txt \
    --output_format srt \
    --fp16 False \
    ${LANG_ARGS[@]+"${LANG_ARGS[@]}"} >&2 2>>"$OUTDIR/.whisper.log" || true
  # Whisper names outputs after the input basename (audio.txt / audio.srt)
  [ -f "$OUTDIR/audio.txt" ] && mv -f "$OUTDIR/audio.txt" "$OUTDIR/transcript.txt"
  [ -f "$OUTDIR/audio.srt" ] && mv -f "$OUTDIR/audio.srt" "$OUTDIR/transcript.srt"
else
  echo "[5/5] Skipping transcription (no audio)." >&2
  printf '(no audio track)\n' > "$OUTDIR/transcript.txt"
fi

# ---------------------------------------------------------------------------
# Summary (stdout — this is what Claude reads back)
# ---------------------------------------------------------------------------
echo ""
echo "=== VIDEO BREAKDOWN READY ==="
echo "Output dir: $OUTDIR"
echo "  video.mp4        full video"
echo "  audio.mp3        $([ "$HAS_AUDIO" -eq 1 ] && echo 'audio track' || echo '(none)')"
echo "  transcript.txt   plain transcript"
echo "  transcript.srt   timestamped transcript"
echo "  frames/          $NFRAMES frames @ ${FPS}fps (timestamp top-left)"
echo "  sheets/          $NSHEETS contact sheet(s)"
echo ""
echo "Next: read sheets/ first for the visual flow, then frames/ for detail,"
echo "and transcript.srt to align what's on screen with what's said."
