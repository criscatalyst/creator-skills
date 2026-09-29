#!/usr/bin/env python3
"""mindcraft_gen.py — generate IG-carousel-ready images via MindCraft Studio (MLX, local).

Three modes:
  --mode pipeline (default)  gen 768x960 → RealESRGAN 4x → LANCZOS down to 1080x1350
                             ~71s/img on M-series. Crisp over-sampled output. IG-ready.
  --mode baseline            direct gen at requested w/h, no upscale.
                             ~126s for 1080x1350. Simpler, slower.
  --mode gen-only            gen only at requested w/h, no upscale/resize.
                             Fastest for quick previews.

Both the gen output AND the upscaled-resized version are saved to MindCraft's
project folder so they appear in the app's canvas/gallery — no scattered duplicates.

Progress UI auto-adapts to TTY:
  - terminal     → animated \r-overwriting bar with spinner + step + elapsed
  - non-tty/pipe → newline snapshots every 3s so output stays readable when captured

Backend port is auto-discovered (dynamic since MindCraft 2.4.2). The app must be open.

Deep reference (endpoints, schema, gotchas): wiki/tech/mindcraft-studio.md
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import subprocess
import sys
import threading
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

# ─── Defaults ──────────────────────────────────────────────────────────────────

import os as _os

# MindCraft Studio default install path is ~/Documents/Modelli MindCraft/
# Override via env vars MINDCRAFT_MODEL_PATH / MINDCRAFT_UPSCALER_PATH if you installed elsewhere.
_MC_ROOT = _os.environ.get("MINDCRAFT_MODELS_ROOT",
                            _os.path.expanduser("~/Documents/Modelli MindCraft"))
MODEL_GEN_DEFAULT = _os.environ.get("MINDCRAFT_MODEL_PATH",
                                     f"{_MC_ROOT}/Base Model/Z-Image-Turbo-mflux-4bit")
MODEL_UP_DEFAULT = _os.environ.get("MINDCRAFT_UPSCALER_PATH",
                                    f"{_MC_ROOT}/Upscaler/realesrgan-mlx")
PROJECT_ROOT = Path.home() / "Library/Containers/cc.themindstudio.mindcraft/Data/Library/Application Support/MindCraft Studio/projects"

# IG carousel canonical format (4:5 portrait)
IG_W, IG_H = 1080, 1350
# Gen resolution used in pipeline mode (4:5, divisible by 64, RealESRGAN-friendly)
PIPELINE_GEN_W, PIPELINE_GEN_H = 768, 960

SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

# ─── Backend discovery + HTTP helpers ──────────────────────────────────────────

def discover_port() -> int:
    """Find MindCraft backend port from the running process (dynamic post-v2.4.2)."""
    try:
        pid = subprocess.check_output(["pgrep", "-f", "MindCraft Studio Backend"]).decode().split()[0]
    except subprocess.CalledProcessError:
        raise RuntimeError("MindCraft Studio not running — open the app first")
    out = subprocess.check_output(["lsof", "-p", pid, "-iTCP", "-sTCP:LISTEN", "-n", "-P"]).decode()
    for line in out.splitlines():
        if "LISTEN" not in line:
            continue
        port = line.split()[8].rsplit(":", 1)[1]
        try:
            r = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2).read().decode()
            if "MindCraft" in r:
                return int(port)
        except Exception:
            pass
    raise RuntimeError("MindCraft process found but no responsive backend port")


def post(port: int, path: str, body: dict, timeout: int = 900) -> dict:
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def get_json(port: int, path: str, timeout: int = 10) -> dict:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=timeout) as r:
        return json.loads(r.read().decode())


def latest_image_in_project(port: int, project: str) -> dict | None:
    """Return the metadata of the most recently saved image in `project`, or None."""
    data = get_json(port, f"/mobile/projects/{project}/images")
    imgs = sorted(data.get("images", []), key=lambda x: -x["timestamp"])
    return imgs[0] if imgs else None


# ─── Progress bar ──────────────────────────────────────────────────────────────

@dataclass
class ProgressState:
    """Shared state between the status poller and the bar renderer."""
    last: dict | None = None
    finalize_started: float | None = None  # marks when status hit "progress=100 still generating"


def _poll_status(port: int, stop: threading.Event, state: ProgressState, status_path: str) -> None:
    while not stop.is_set():
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{status_path}", timeout=2) as r:
                state.last = json.loads(r.read().decode())
        except Exception:
            pass
        time.sleep(0.5)


def _render_tty(state: ProgressState, started: float, label: str, width: int = 30) -> str:
    """Animated single-line bar. Overwrites with \\r. Use only on a real terminal."""
    s = state.last or {}
    status = s.get("status", "")
    step = s.get("step", 0)
    total = s.get("total_steps", 0) or 0
    pct = s.get("progress", 0)
    msg = s.get("message") or "warming up…"
    elapsed = int(time.time() - started)
    spinner = SPINNER[int(time.time() * 10) % 10]

    in_post = status == "generating" and total > 0 and pct >= 99.9
    if in_post:
        if state.finalize_started is None:
            state.finalize_started = time.time()
        post_el = int(time.time() - state.finalize_started)
        return (f"\r{spinner} {label}  [{'█'*width}]  step {step:>2}/{total:<2}  "
                f"✓ +{post_el:>3}s  total {elapsed:>4}s  Finalizing (VAE+save)…   ")
    filled = int(width * pct / 100)
    bar = "█" * filled + "░" * (width - filled)
    step_str = f"{step}/{total}" if total else "—"
    return (f"\r{spinner} {label}  [{bar}]  step {step_str:>5}  "
            f"{pct:3.0f}%  total {elapsed:>4}s  {msg[:55]:<55}")


def _render_snapshot(state: ProgressState, started: float, label: str) -> tuple[str, str]:
    """Multi-line snapshot for non-TTY (captured by parent process)."""
    s = state.last or {}
    status = s.get("status", "...")
    step = s.get("step", 0)
    total = s.get("total_steps", 0) or 0
    pct = s.get("progress", 0)
    msg = s.get("message") or "warming up…"
    elapsed = int(time.time() - started)
    in_post = status == "generating" and total > 0 and pct >= 99.9
    if in_post:
        if state.finalize_started is None:
            state.finalize_started = time.time()
        post_el = int(time.time() - state.finalize_started)
        line = f"  [{elapsed:>4}s]  {label}: step {step}/{total}  ✓ diffusion done  → finalizing +{post_el}s (VAE+save)"
        key = "post"
    else:
        line = f"  [{elapsed:>4}s]  {label}: step {step}/{total or '?'}  {pct:3.0f}%  {msg[:55]}"
        key = f"{step}/{total}/{int(pct)}/{status}"
    return line, key


def watch_progress(port: int, status_path: str, label: str, is_alive_fn) -> None:
    """Block until `is_alive_fn()` returns False, showing a progress bar / snapshots."""
    state = ProgressState()
    stop = threading.Event()
    started = time.time()
    threading.Thread(target=_poll_status, args=(port, stop, state, status_path), daemon=True).start()

    use_tty = sys.stdout.isatty()
    if use_tty:
        while is_alive_fn():
            sys.stdout.write(_render_tty(state, started, label))
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * 130 + "\r")
        sys.stdout.flush()
    else:
        # Non-TTY (captured by Bash tool, pipe, etc): print newline snapshots only on
        # MEANINGFUL state changes (step bump / phase transition) — no time-based spam.
        # Result: ~6-10 lines per 150s gen, readable when shown in chat after completion.
        last_key = ""
        while is_alive_fn():
            line, key = _render_snapshot(state, started, label)
            if key != last_key:
                print(line, flush=True)
                last_key = key
            time.sleep(0.5)

    stop.set()


# ─── Pipeline phases ───────────────────────────────────────────────────────────

def phase_generate(port: int, prompt: str, *, w: int, h: int, steps: int, guidance: float,
                   seed: int | None, model_path: str, memory_mode: str, project: str) -> dict:
    """POST /generate (blocking); concurrent thread watches /generation-status."""
    body = {
        "prompt": prompt,
        "project_id": project,
        "model_path": model_path,
        "width": w, "height": h,
        "steps": steps, "guidance_scale": guidance,
        "memory_mode": memory_mode,
    }
    if seed is not None:
        body["seed"] = seed

    result: dict = {"data": None, "error": None}
    def _do():
        try:
            result["data"] = post(port, "/generate", body)
        except Exception as e:
            result["error"] = e

    poster = threading.Thread(target=_do, daemon=True)
    poster.start()
    watch_progress(port, "/generation-status", f"GEN {w}x{h}", poster.is_alive)
    if result["error"]:
        raise result["error"]
    return result["data"]


def phase_upscale(port: int, image_path: str, *, model_path: str, memory_mode: str) -> bytes:
    """POST /upscale (blocking); returns raw PNG bytes. RealESRGAN-MLX is hard-coded to 4x."""
    body = {
        "image_path": image_path,
        "upscaler_model_path": model_path,
        "scale_factor": 4,  # ignored by MLX RealESRGAN — always produces 4x
        "upscaler_type": "realesrgan",
        "memory_mode": memory_mode,
    }
    result: dict = {"data": None, "error": None}
    def _do():
        try:
            result["data"] = post(port, "/upscale", body)
        except Exception as e:
            result["error"] = e

    poster = threading.Thread(target=_do, daemon=True)
    poster.start()
    watch_progress(port, "/upscale-status", "UPSCALE 4x", poster.is_alive)
    if result["error"]:
        raise result["error"]

    b64 = result["data"]["image"]
    if b64.startswith("data:image/"):
        b64 = b64.split(",", 1)[1]
    return base64.b64decode(b64)


def phase_resize_to_ig(png_bytes: bytes, *, w: int = IG_W, h: int = IG_H) -> bytes:
    """LANCZOS downsample to IG carousel format. Returns optimized PNG bytes."""
    try:
        from PIL import Image
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "--user", "Pillow"])
        from PIL import Image
    img = Image.open(io.BytesIO(png_bytes))
    out = io.BytesIO()
    img.resize((w, h), Image.LANCZOS).save(out, format="PNG", optimize=True)
    return out.getvalue()


def save_to_project(project: str, basename: str, png_bytes: bytes) -> Path:
    """Drop the PNG into MindCraft's project images/ folder. Auto-detected by the app."""
    proj_dir = PROJECT_ROOT / project / "images"
    proj_dir.mkdir(parents=True, exist_ok=True)
    ts_ms = int(time.time() * 1000)
    dest = proj_dir / f"{ts_ms}_{basename}.png"
    dest.write_bytes(png_bytes)
    return dest


# ─── CLI ───────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--mode", choices=["pipeline", "baseline", "gen-only"], default="pipeline",
                    help="pipeline = gen 768→upscale 4x→resize 1080x1350 (default, ~71s)")
    ap.add_argument("--project", default="default", help="MindCraft project id")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--width", type=int, default=None, help="override gen width (default depends on --mode)")
    ap.add_argument("--height", type=int, default=None)
    ap.add_argument("--steps", type=int, default=4)
    ap.add_argument("--guidance", type=float, default=3.5)
    ap.add_argument("--memory-mode", default="speed", choices=["balance", "speed", "low"])
    ap.add_argument("--model-path", default=MODEL_GEN_DEFAULT)
    ap.add_argument("--upscaler-path", default=MODEL_UP_DEFAULT)
    ap.add_argument("--keep-source", action="store_true",
                    help="In pipeline mode, keep the low-res gen in MindCraft project (default: delete after upscale to avoid duplicates)")
    args = ap.parse_args()

    # Resolve gen resolution per mode
    if args.mode == "pipeline":
        gen_w, gen_h = args.width or PIPELINE_GEN_W, args.height or PIPELINE_GEN_H
    else:
        gen_w, gen_h = args.width or IG_W, args.height or IG_H

    port = discover_port()
    print(f"→ Backend     : 127.0.0.1:{port}")
    print(f"→ Mode        : {args.mode}")
    print(f"→ Project     : '{args.project}'")
    print(f"→ Gen res     : {gen_w}x{gen_h}  steps={args.steps}  guidance={args.guidance}  memory={args.memory_mode}")
    print(f"→ Prompt      : {args.prompt[:90]}{'…' if len(args.prompt) > 90 else ''}")
    print()

    t_start = time.time()

    # Phase 1: generate (saved to MindCraft project via project_id)
    gen_data = phase_generate(
        port, args.prompt, w=gen_w, h=gen_h, steps=args.steps, guidance=args.guidance,
        seed=args.seed, model_path=args.model_path, memory_mode=args.memory_mode,
        project=args.project,
    )
    t_gen = time.time()
    print(f"✓ Gen done in {t_gen-t_start:.1f}s  (API: {gen_data.get('generation_time_ms',0)/1000:.1f}s)  "
          f"seed={gen_data.get('seed')}")

    if args.mode == "gen-only":
        print(f"\n=== TOTAL: {time.time()-t_start:.1f}s — open MindCraft to view ===")
        return 0

    # Find the just-saved image path
    img_meta = latest_image_in_project(port, args.project)
    if not img_meta:
        print("✗ Couldn't locate the saved image — abort upscale", file=sys.stderr)
        return 2
    src_path = img_meta["path"]
    print(f"  saved as: {img_meta['filename']}")

    if args.mode == "baseline":
        # Baseline does not upscale; gen was at IG res already
        print(f"\n=== TOTAL: {time.time()-t_start:.1f}s — IG-ready, open MindCraft to view ===")
        return 0

    # Phase 2: upscale (4x — MLX RealESRGAN hard-coded)
    print()
    up_bytes = phase_upscale(port, src_path, model_path=args.upscaler_path, memory_mode=args.memory_mode)
    t_up = time.time()
    print(f"✓ Upscale done in {t_up-t_gen:.1f}s  ({len(up_bytes):,} bytes upscaled)")

    # Phase 3: resize to IG canonical
    print()
    ig_bytes = phase_resize_to_ig(up_bytes)
    t_resize = time.time()
    print(f"✓ Resize to {IG_W}x{IG_H} done in {t_resize-t_up:.2f}s  ({len(ig_bytes):,} bytes)")

    # Cleanup: delete the low-res 768×960 source so MindCraft project only has the final 1080×1350.
    # Cris's preference — avoid duplicates inside the app gallery. Opt out via --keep-source.
    if not args.keep_source:
        try:
            Path(src_path).unlink()
            # MindCraft may also write a thumbnails/<file>.jpg companion — try to delete it too.
            thumb = Path(src_path).parent / "thumbnails" / Path(src_path).name.replace(".png", ".jpg")
            if thumb.exists():
                thumb.unlink()
            print(f"  cleaned : {Path(src_path).name} (low-res source removed from project)")
        except Exception as e:
            print(f"  ⚠ couldn't delete source {src_path}: {e}", file=sys.stderr)

    # Save 1080x1350 back to MindCraft project (auto-detected by app via folder scan)
    seed_tag = f"_seed{args.seed}" if args.seed is not None else ""
    dest = save_to_project(args.project, f"ig1080{seed_tag}", ig_bytes)
    print(f"  saved to project as: {dest.name}")

    total = time.time() - t_start
    print(f"\n=== TOTAL: {total:.1f}s  ({(126-total)/126*100:+.0f}% vs 126s direct baseline) ===")
    print(f"  Gen 768x960   : {t_gen-t_start:6.1f}s  ({(t_gen-t_start)/total*100:.0f}%)")
    print(f"  Upscale 4x    : {t_up-t_gen:6.1f}s  ({(t_up-t_gen)/total*100:.0f}%)")
    print(f"  Resize        : {t_resize-t_up:6.2f}s  ({(t_resize-t_up)/total*100:.0f}%)")
    print(f"\n→ Both versions now in MindCraft project '{args.project}' canvas/gallery")
    return 0


if __name__ == "__main__":
    sys.exit(main())
