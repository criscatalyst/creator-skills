---
name: video-breakdown
description: Break a video down into its VISUALS and its AUDIO so you can study exactly what happens on screen and what is said. Downloads the video with yt-dlp, splits the audio track, samples timestamped frames + contact-sheet grids with ffmpeg, and transcribes the audio with local Whisper. Trigger when the user pastes a video URL (Instagram reel, TikTok, YouTube / YT Short, X/Twitter, Vimeo, …) and asks to "analyze the visuals", "break this down", "what happens in this video", "shot-by-shot", "frame by frame", "study this reel", or wants both what is shown and what is said.
---

# Video Breakdown

Reverse-engineer any video — both the **visual** track (what's on screen, shot by shot) and the **audio** track (the transcript) — using only local tools. No API key, nothing uploaded.

## When to use

- User pastes a video URL and wants to know **what happens on screen** (not just the words).
- Studying a competitor reel/short: hook visuals, cut pacing, text overlays, b-roll, CTA frame.
- Mapping a video shot-by-shot to recreate or repurpose it.
- Any time the user wants **visuals + transcript together**, aligned by timestamp.

> If the user only wants the spoken words, the lighter `transcribe` skill is enough. Use this one when the **visuals matter**.

## Setup — everything this skill needs to run

The script depends on three command-line tools, and those tools have their own
dependencies. Here is the **full chain** so you know exactly what must be present.

| Tool | Why it's needed | Pulls in / requires |
|---|---|---|
| **Homebrew** | package manager used to install everything below | macOS; see https://brew.sh |
| **`yt-dlp`** | downloads the video | Python 3 (Homebrew installs it automatically as a dependency). **Needs `ffmpeg`** to merge separate video+audio streams. |
| **`ffmpeg`** | splits the audio, samples frames, builds contact sheets, burns timestamps | self-contained |
| **`whisper`** (`openai-whisper`) | local speech-to-text | Python 3 + **PyTorch** (a large dependency, ~2 GB, installed automatically). Uses `ffmpeg` to read audio. On first run it **downloads the model weights** (~75 MB `tiny`, ~500 MB `small`, ~1.5 GB `medium`, ~3 GB `large-v3`) into `~/.cache/whisper/`. |

**Note:** none of this needs Java, Node, or Docker. The only heavy one-time pulls are
PyTorch (via the whisper install) and the Whisper model weights (on the first
transcription). yt-dlp does **not** work without ffmpeg for many sites, which is why
ffmpeg is non-optional even though it looks separate.

### Step 1 — verify the chain (when the script reports a missing tool, or on a new machine)

`breakdown.sh` checks its own dependencies and exits `10` with the exact install line, so on a
machine where it has already run you can go straight to "How to run".

```bash
echo "Homebrew:"; command -v brew && brew --version | head -1
echo "yt-dlp:";   command -v yt-dlp && yt-dlp --version
echo "ffmpeg:";   command -v ffmpeg && ffmpeg -version | head -1
echo "whisper:";  command -v whisper && whisper --help >/dev/null 2>&1 && echo "ok"
echo "python3:";  command -v python3 && python3 --version
```

Read the output. If a line shows nothing after the label, that tool is missing.

### Step 2 — install whatever is missing

Installing software changes the user's system — **get a yes from the user first**, then:

```bash
# If Homebrew itself is missing, the user must install it (it prompts for a password):
#   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Then install the three tools (Python + PyTorch come along automatically):
brew install yt-dlp ffmpeg openai-whisper
```

If only one is missing, install just that one (e.g. `brew install ffmpeg`).

### Step 3 — make the script executable (first use only)

```bash
chmod +x "${CLAUDE_SKILL_DIR}/breakdown.sh"
```

The script also re-checks dependencies itself and exits with code `10` plus the exact
`brew install …` line if anything is still missing — so a missing tool never fails silently.

## How to run

```bash
"${CLAUDE_SKILL_DIR}/breakdown.sh" "<URL>" [fps] [whisper_model] [language] [outdir]
```

| Arg | Default | Notes |
|---|---|---|
| `fps` | `1` | Frames sampled per second. Use `0.5` for long videos, `2` for fast-cut reels. |
| `whisper_model` | `small` | `medium` for accents/noise, `tiny`/`base` for speed, `large-v3` for best quality. |
| `language` | auto | Pass `en` / `it` / … if auto-detect mis-fires on short clips. |
| `outdir` | `./video-breakdown-<timestamp>` | Where everything lands. |

**Pick `fps` before running.** Estimate the video length:
- Short reel / TikTok (≤60s): `1` (default) is good — ~30–60 frames.
- Fast-cut / heavy text-overlay reel: `2`.
- Long video (several minutes): `0.5` or lower, or you'll generate hundreds of frames. Warn the user about the wait first.

The script prints a summary to stdout when done.

## How to read the output and analyze

After the script finishes, work through the output dir in this order:

1. **`sheets/sheet_*.png` first — the visual overview.** Each sheet is a 5×6 grid of frames with the timestamp burned into each thumbnail. Read these images to get the whole flow of the video at a glance: scene changes, on-screen text, b-roll vs talking head, where the cuts land.
2. **`frames/frame_*.jpg` for detail.** When a specific moment matters (the hook frame, a text overlay, the CTA), read the individual frame — it's higher resolution. Each frame has its timestamp top-left, so you can name the exact second.
3. **`transcript.srt` to align audio to visuals.** The `.srt` has timestamped segments. Match each spoken line to what's on screen at that timestamp. `transcript.txt` is the plain version if you just want the words.

Then synthesize for the user. Don't dump raw frames — deliver a **breakdown**:
- **Shot-by-shot timeline**: `0:00–0:02 hook frame (text: "…", talking head)`, `0:02–0:05 b-roll of …`, etc.
- **Hook analysis**: what's on screen + said in the first 3 seconds, and why it stops the scroll.
- **Visual devices**: text overlays, captions style, cut rhythm, zoom/punch-ins, b-roll ratio.
- **Structure beats**: hook → build-up → value → CTA, with the timestamp of each.
- **CTA frame**: what the final frame shows and says.

Ask the user what they're after (recreate it? steal the hook? study pacing?) and tailor the depth.

## Self-debugging playbook

If the script errors or the output looks wrong, **diagnose it yourself before asking the user.**
You have everything you need: the exit code, the on-screen step log (`[1/5]…[5/5]`), and two
log files written into the output dir.

### Where the evidence is

- **Exit code** — tells you which stage failed:
  | Code | Meaning | First move |
  |---|---|---|
  | `1` | bad/missing arguments | re-read the usage and re-run with a URL |
  | `10` | a dependency is missing | run the Step-1 verify block, then install the named tool |
  | `2` | yt-dlp produced no video | see "Download failed" below |
  | non-zero from ffmpeg/whisper | read the log files | see below |
- **`<outdir>/.ffmpeg.log`** — full ffmpeg stderr for the audio-split, frame, and contact-sheet steps.
- **`<outdir>/.whisper.log`** — full whisper stderr (model load, CUDA/MPS notices, errors).
- Inspect them with: `tail -30 <outdir>/.ffmpeg.log` and `tail -30 <outdir>/.whisper.log`.

### Common failures → fix

- **Download failed (exit 2) on Instagram/TikTok** → almost always login-walled or private.
  Re-run the script after editing the yt-dlp call to add cookies, e.g.:
  `--cookies-from-browser safari` (or `chrome`, `firefox`). Tell the user they must be logged
  into that site in that browser.
- **Download failed + a `SABR` / "missing a URL" / 403 warning on YouTube** → yt-dlp is out of
  date relative to a site change. Fix: `brew upgrade yt-dlp` (or `yt-dlp -U`), then re-run. This
  is the single most common YouTube breakage.
- **"ffmpeg not found" mid-download** → yt-dlp downloaded streams but can't merge them. Install
  ffmpeg (`brew install ffmpeg`) and re-run.
- **`frames/` is empty but the video downloaded** → check `.ffmpeg.log`. Usually a corrupt
  download (re-run) or an exotic codec (re-run; ffmpeg transcodes on read).
- **Frames have no burned-in timestamp** → no TTF font was found on the system. The frames are
  still valid; frame N is at ≈ `N / fps` seconds. To restore the overlay, install a font
  (`brew install --cask font-dejavu`) or note times by frame index.
- **`transcript.txt` says "(no audio track)"** → the video is silent / music-only. Expected;
  do the visual breakdown only.
- **Transcript is empty or in the wrong language** → re-run with an explicit `language` arg
  (`en`, `it`, …). Very short clips fool auto-detect.
- **Whisper is extremely slow / seems hung** → it runs on CPU and a large model on a long video
  takes minutes. Re-run with a smaller model (`tiny`/`base`) and/or a lower `fps`. The
  `.whisper.log` shows progress.
- **Hundreds of frames / giant sheets** → `fps` was too high for the video length. Re-run lower
  (`0.5` or less).
- **"command not found: brew"** → Homebrew isn't installed; the user must install it first
  (see Setup Step 2).

After a fix, re-run the whole script: it's idempotent (it writes into a fresh or the given
outdir). Escalate to the user only for what needs them: private content that needs their login,
or a missing Homebrew that needs their password.

## Stack

- `yt-dlp` — downloads the video from almost any site (needs ffmpeg + Python)
- `ffmpeg` — splits the audio, samples frames, builds contact sheets, burns timestamps
- `openai-whisper` — local speech-to-text, timestamped `.srt` (needs Python + PyTorch)

Everything runs locally. Zero cost. First Whisper run downloads model weights (~500MB `small`), cached in `~/.cache/whisper/`.
