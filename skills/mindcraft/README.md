# MindCraft — Claude Code skill

> Part of [**creator-skills**](../../README.md). Install as a plugin: `/plugin install mindcraft@creator-skills` (manual install below).

> **Local AI image generation for Claude Code.** Generate cinematic, editorial-tier images on your Mac using [MindCraft Studio](https://themindstudio.cc/mindcraft) + Z-Image Turbo. **$0 per image, no rate limits, ~70s for a 1080×1350 IG-ready slide.**

Built for creators who want Midjourney-tier output without the subscription, the rate limits, or the "is this prompt worth the cost" anxiety.

---

## What it does

A Python helper (`mindcraft_gen.py`) wraps the MindCraft Studio local HTTP API into a clean CLI:

```bash
./mindcraft_gen.py \
  --prompt "cinematic editorial photography, lone tree on golden wheat field, fine film grain, magazine quality" \
  --seed 42
```

Output: a 1080×1350 IG-carousel-ready PNG saved directly into your MindCraft project gallery.

**Three modes:**

| `--mode` | Pipeline | Time | Use for |
|---|---|---|---|
| `pipeline` (default) | gen 768×960 → RealESRGAN 4x → resize 1080×1350 | ~71s | IG carousel slides, final assets |
| `baseline` | direct gen at requested w/h, no upscale | ~126s for 1080×1350 | Specific non-IG resolutions |
| `gen-only` | gen only, no upscale/resize | ~30-55s | Quick previews |

In pipeline mode the helper auto-cleans the low-res source from your project after upscaling, so your MindCraft gallery only keeps the final 1080×1350.

---

## Setup

### 1. Install MindCraft Studio
Download from [themindstudio.cc/mindcraft](https://themindstudio.cc/mindcraft) (free, macOS only, Apple Silicon required).

### 2. Install Z-Image Turbo model
Inside the MindCraft app: go to Models → download **Z-Image Turbo (4-bit)** (~5 GB). This is the fast Apple Silicon-optimized image gen model.

Optional but recommended:
- **RealESRGAN MLX** (Upscaler) — needed for `--mode pipeline`. Download from the in-app Upscaler section.
- **Qwen3-VL 4B** (AI Prompt) — needed for prompt optimization / vision features.

### 3. Install Python deps
```bash
pip3 install --user Pillow
```

(That's it. `mindcraft_gen.py` uses only stdlib + Pillow for image post-processing.)

### 4. Install the skill
```bash
git clone https://github.com/criscatalyst/creator-skills.git ~/creator-skills
ln -s ~/creator-skills/skills/mindcraft ~/.claude/skills/mindcraft
chmod +x ~/creator-skills/skills/mindcraft/mindcraft_gen.py
```

Or as a plugin: `/plugin install mindcraft@creator-skills`. The usage examples below run from the skill folder.

### 5. (Optional) Configure model paths
If you installed MindCraft models in a non-default location, set env vars:
```bash
export MINDCRAFT_MODELS_ROOT="$HOME/path/to/Modelli MindCraft"
# Or override individual model paths:
export MINDCRAFT_MODEL_PATH="$HOME/.../Z-Image-Turbo-mflux-4bit"
export MINDCRAFT_UPSCALER_PATH="$HOME/.../realesrgan-mlx"
```

The defaults assume MindCraft's standard install path: `~/Documents/Modelli MindCraft/`.

---

## Usage examples

### Single image
```bash
./mindcraft_gen.py --prompt "cinematic editorial photo, single empty chair floating on calm pale grey sea, soft golden hour light, surreal mood, magazine quality" --seed 7
```

### Specific resolution (skip pipeline)
```bash
./mindcraft_gen.py --prompt "..." --mode baseline --width 1280 --height 720
```

### Quick preview (gen only, no upscale)
```bash
./mindcraft_gen.py --prompt "..." --mode gen-only --width 512 --height 512
```

### Keep both 768 and 1080 versions in project
```bash
./mindcraft_gen.py --prompt "..." --keep-source
```

### List all flags
```bash
./mindcraft_gen.py --help
```

---

## Prompt patterns that work well

The helper is tuned for **cinematic editorial** output. Base template:

```
cinematic editorial photography, [SUBJECT], [LIGHTING], [MOOD], magazine quality, fine film grain, shallow depth of field
```

Tested mood archetypes:

| Mood | Pattern |
|---|---|
| **Surreal/cinematic** | `[SUBJECT] floating/suspended in [ENV], soft [TIME-OF-DAY] light, surreal magazine quality` |
| **Natural paesaggio** | `single figure walking through [LANDSCAPE], golden hour amber light, contemplative mood` |
| **Dark drama** | `lone [SUBJECT] in deep dark [ENV], single beam of warm amber light, deep shadows, surreal contemplative mood` |
| **Workspace** | `dark moody [ROOM] with single [OBJECT] glowing, warm window light bleeding in, plants on shelves, magazine quality` |

Z-Image Turbo is photorealistic-strong but weak on legible text-in-image — avoid prompts that need readable signs/labels.

---

## How it works under the hood

1. **Port discovery**: MindCraft's backend port is dynamic (post-v2.4.2). Helper discovers it via `lsof` on the MindCraft backend process.
2. **Generate**: POST `/generate` with prompt + model_path + project_id → saves into your MindCraft project automatically.
3. **Upscale** (pipeline only): POST `/upscale` on the saved file → RealESRGAN MLX → 4x upscaled (NB: `scale_factor` param is ignored by RealESRGAN MLX, always 4x).
4. **Resize** (pipeline only): LANCZOS downsample 3072×3840 → 1080×1350. Over-sampling preserves sharpness.
5. **Cleanup** (pipeline only): delete the low-res source from project so only the final 1080×1350 remains. Opt out with `--keep-source`.

Progress is reported in TTY mode as a live animated bar; in non-TTY mode (e.g. captured by another script), as newline snapshots on state change.

---

## Use it with Claude Code

Once installed (step 4), just ask in Claude Code:

```bash
> /mindcraft Generate a cinematic editorial photo of a samurai walking through fresh snow at dawn
```

Claude will read `SKILL.md`, understand the helper's CLI, and run it for you with a prompt tuned to your request.

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `MindCraft Studio not running — open the app first` | Open MindCraft.app. The backend is a child process of the GUI. |
| First gen takes 60+s of "model load" before progressing | Normal — Z-Image loads into MLX memory on first call. Subsequent gens are fast. |
| White borders around generated image | Z-Image MLX sometimes adds ~5% white margin. The helper auto-crops this. |
| `Executable doesn't exist at ...chromium...` | You're trying to use this in Playwright context. This helper doesn't need Playwright — just Pillow. |
| `ModuleNotFoundError: PIL` | `pip3 install --user Pillow` |

For deeper API details (all 67 MindCraft endpoints, /upscale, /images/describe VLM, /image-utils/expand outpainting, etc.) see the [MindCraft Studio docs](https://themindstudio.cc/mindcraft/docs).

---

## License

MIT. Use freely. Attribution appreciated but not required.

If this saves you a Midjourney subscription, consider [following @criscatalyst on Instagram](https://instagram.com/criscatalyst) for more creator-operator tooling.
