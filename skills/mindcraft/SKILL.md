---
name: mindcraft
description: "Local AI image generation via MindCraft Studio (MLX, Apple Silicon). Generate cinematic-editorial images locally, $0 per image, no rate limits, ~70s for 1080×1350 IG-ready output. Use when the user wants to generate, upscale, or batch-create images for carousels, posts, thumbnails, or any visual asset. Triggers: generate image, create image, mindcraft, local image gen, AI image, cinematic background, carousel background, IG carousel image, thumbnail."
---

# MindCraft Skill — Local AI Image Generation

You have access to a Python helper (`mindcraft_gen.py`) that wraps the local MindCraft Studio HTTP API. Use it when the user wants images generated for any purpose — carousel slides, thumbnails, hero images, social posts, etc.

## When to use this skill

Trigger phrases:
- "generate an image of X"
- "make me a cinematic photo of X"
- "I need a background for my carousel"
- "create a thumbnail showing X"
- "mindcraft / local image gen / AI image"

DO NOT use this skill for:
- Stock photos (use Unsplash/Pexels MCP instead)
- Reusing images the user has on disk (just `Read` them)
- Logo/icon work (better via Canva or vector tools)

## Pre-flight checks

Before running:

1. **Confirm MindCraft is running**: `pgrep -f "MindCraft Studio Backend"` should return a PID. If empty → tell user to open MindCraft.app.
2. **Confirm Mac is Apple Silicon**: skill requires MLX which only works on M-series chips. If x86, abort.
3. **Confirm models installed**: at minimum need `Z-Image Turbo (4-bit)` in `~/Documents/Modelli MindCraft/Base Model/`. For pipeline mode also need `realesrgan-mlx` upscaler.

## Default workflow

```bash
cd "${CLAUDE_SKILL_DIR}"
./mindcraft_gen.py --prompt "<TUNED_PROMPT>" --seed <N>
```

For IG carousel work, use `--mode pipeline` (default): generates 1080×1350 IG-ready output in ~71s, saved to the user's MindCraft default project.

## Prompt engineering

When the user gives a rough idea, **tune the prompt** before calling the helper. Template:

```
cinematic editorial photography, [SUBJECT_FROM_USER], [INFERRED_LIGHTING], [INFERRED_MOOD], magazine quality, fine film grain, shallow depth of field
```

Add specifics:
- **Subject**: keep the user's intent verbatim, add 1-2 descriptive details
- **Lighting**: pick based on mood — "soft golden hour amber light" (warm), "cool blue moonlight" (dramatic), "soft natural window light" (intimate)
- **Mood**: "surreal", "contemplative", "cinematic", "dramatic", "calm" — pick one

### Examples of prompt tuning

User says: "image of a person at a desk"
You tune to: `cinematic editorial photography, single figure seen from behind sitting at a wide minimalist desk with one ultrawide monitor glowing in a dark home office, warm window light bleeding from the side, plants on shelves, magazine quality, fine film grain, shallow depth of field`

User says: "samurai in snow for my reel cover"
You tune to: `cinematic editorial photography, lone samurai with conical hat walking through fresh deep snow at cold dawn, dramatic backlighting from soft pale light, surreal contemplative mood, magazine quality, fine film grain, shallow depth of field`

## After generation

1. **Find the output**: the helper saves to the user's MindCraft default project at `~/Library/Containers/cc.themindstudio.mindcraft/Data/Library/Application Support/MindCraft Studio/projects/default/images/<timestamp>_<seed>_ig1080.png`
2. **Show it inline**: `Read` the file path to display the image in chat — user reviews quality
3. **If user wants tweak**: re-run with different seed or refined prompt. Don't fight a single seed — try 3-5 variations and let the user pick.

## Batch generation

For multiple images (e.g. 7 carousel slides), use `run_in_background=true` on the Bash call and poll periodically (`tail` the task output file) so user sees periodic progress updates in chat.

Single gen: ~71s in pipeline mode. 7 gens batch: ~8-10 min total.

## Common follow-ups

- "Now make a version of this with X" → reuse same seed, change SUBJECT/LIGHTING in prompt
- "Make it darker / lighter / more dramatic" → adjust LIGHTING and MOOD words
- "I want the same vibe but with Y subject" → keep LIGHTING + MOOD, swap SUBJECT, randomize seed

## What this skill does NOT cover

The helper handles `/generate` + `/upscale` + resize. For these other MindCraft features, refer the user to the MindCraft Studio docs directly:
- `/images/describe` (VLM image-to-text description)
- `/image-utils/inpaint` (mask-based editing)
- `/image-utils/expand` (outpainting)
- Custom workflows in the Infinite Canvas GUI

The helper is opinionated for batch-friendly editorial image generation. For one-off creative editing, the user should work directly in the MindCraft GUI.

## Output guidance

When showing the user the generated image, include:
- The exact prompt you used (so they can iterate)
- The seed (so they can reproduce)
- Total time taken
- Where the file is saved (path)

Example reply:
> ✓ Generated in 68s. Saved as `<filename>` in your MindCraft default project.
> Prompt: `cinematic editorial photography, lone samurai...`
> Seed: 42

If the output isn't what they wanted, suggest 1-2 specific prompt adjustments (not a wall of options) and offer to regenerate.
