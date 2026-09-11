#!/usr/bin/env python3
"""Assemble NestWeaver README demo GIFs from AI-generated photoreal keyframes.

The GIFs are **AI-generated photorealistic product visualizations** — not live
footage of a shipped unit. Keyframes live under ``docs/media/frames/<scene>/``
and this script crossfade-interpolates them into ~5s animated GIFs optimized
for GitHub README embedding.

Workflow
--------
1. Generate consistent photoreal keyframes (Cursor GenerateImage or similar)
   using a locked NestWeaver robot reference design.
2. Place numbered PNGs in ``docs/media/frames/{navigate,pick,deliver,voice,tidy}/``.
3. Run::

     .venv/bin/python scripts/generate_demo_gifs.py

Requires Pillow. Optionally uses ffmpeg for palette-optimized GIF encoding
when available (smaller, cleaner dithering).
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

try:
    from PIL import Image
except ImportError as exc:
    raise SystemExit(
        "Pillow is required. Install with: pip install Pillow\n" + str(exc)
    ) from exc

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "media"
FRAMES = OUT / "frames"
SIZE = (720, 405)  # 16:9, README-friendly
DURATION_S = 5.0
FPS = 24
INTERP_PER_GAP = None  # computed from keyframe count to hit ~DURATION_S

SCENES = {
    "navigate": "demo-navigate.gif",
    "pick": "demo-pick-bottle.gif",
    "deliver": "demo-deliver.gif",
    "voice": "demo-voice-llm.gif",
    "tidy": "demo-tidy.gif",
}


def _load_keyframes(scene_dir: Path) -> list[Image.Image]:
    paths = sorted(scene_dir.glob("*.png")) + sorted(scene_dir.glob("*.jpg"))
    if len(paths) < 2:
        raise SystemExit(f"Need >=2 keyframes in {scene_dir}")
    frames: list[Image.Image] = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        im = im.resize(SIZE, Image.Resampling.LANCZOS)
        frames.append(im)
    return frames


def _interp_sequence(keys: list[Image.Image], total_frames: int) -> list[Image.Image]:
    """Crossfade between keyframes to produce ``total_frames`` outputs."""
    n_gaps = len(keys) - 1
    # Distribute frames across gaps (last keyframe held for remainder).
    base = total_frames // n_gaps
    rem = total_frames % n_gaps
    out: list[Image.Image] = []
    for g in range(n_gaps):
        steps = base + (1 if g < rem else 0)
        a, b = keys[g], keys[g + 1]
        for s in range(steps):
            t = s / max(steps, 1)
            # Ease in-out for less slideshow feel.
            t = t * t * (3 - 2 * t)
            blended = Image.blend(a, b, t)
            out.append(blended)
    # Ensure exact length.
    while len(out) < total_frames:
        out.append(keys[-1].copy())
    return out[:total_frames]


def _encode_gif_pillow(frames: list[Image.Image], dest: Path, fps: int) -> None:
    duration_ms = int(round(1000 / fps))
    # Quantize with adaptive palette per-frame via save_all.
    frames[0].save(
        dest,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
        disposal=2,
    )


def _encode_gif_ffmpeg(frames: list[Image.Image], dest: Path, fps: int) -> bool:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False
    with tempfile.TemporaryDirectory(prefix="nwgif_") as tmp:
        tmp_path = Path(tmp)
        for i, fr in enumerate(frames):
            fr.save(tmp_path / f"f{i:04d}.png")
        palette = tmp_path / "palette.png"
        pattern = str(tmp_path / "f%04d.png")
        # Two-pass palette for better quality/size tradeoff.
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-framerate",
                str(fps),
                "-i",
                pattern,
                "-vf",
                "palettegen=stats_mode=diff",
                str(palette),
            ],
            check=True,
        )
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-framerate",
                str(fps),
                "-i",
                pattern,
                "-i",
                str(palette),
                "-lavfi",
                "paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle",
                str(dest),
            ],
            check=True,
        )
    return True


def build_scene(scene: str, outfile: str) -> dict:
    scene_dir = FRAMES / scene
    keys = _load_keyframes(scene_dir)
    total = int(DURATION_S * FPS)
    seq = _interp_sequence(keys, total)
    dest = OUT / outfile
    used = "ffmpeg"
    try:
        ok = _encode_gif_ffmpeg(seq, dest, FPS)
        if not ok:
            used = "pillow"
            _encode_gif_pillow(seq, dest, FPS)
    except subprocess.CalledProcessError:
        used = "pillow"
        _encode_gif_pillow(seq, dest, FPS)

    size_mb = dest.stat().st_size / (1024 * 1024)
    # If huge, recompress at lower res / fps via pillow.
    if size_mb > 15:
        smaller = [f.resize((640, 360), Image.Resampling.LANCZOS) for f in seq[::2]]
        _encode_gif_pillow(smaller, dest, FPS // 2)
        used = f"{used}+downscale"
        size_mb = dest.stat().st_size / (1024 * 1024)

    return {
        "scene": scene,
        "file": dest.name,
        "keyframes": len(keys),
        "frames": total if "downscale" not in used else total // 2,
        "duration_s": DURATION_S,
        "size_mb": round(size_mb, 2),
        "encoder": used,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for scene, outfile in SCENES.items():
        info = build_scene(scene, outfile)
        results.append(info)
        print(
            f"{info['file']}: {info['keyframes']} keys → "
            f"{info['frames']} frames @ ~{info['duration_s']}s, "
            f"{info['size_mb']} MB ({info['encoder']})"
        )
    print("Done. GIFs written to", OUT)


if __name__ == "__main__":
    main()
