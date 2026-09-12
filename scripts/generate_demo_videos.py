#!/usr/bin/env python3
"""Generate NestWeaver README demo videos via true image-to-video (I2V).

Primary path (required for shipping demos)
------------------------------------------
Call a generative I2V API / Space, write H.264 MP4 under ``docs/media/``, then
encode a GIF **from those video frames** (ffmpeg palette) for GitHub README
fallback.

Backends (tried in order by ``--backend auto``):

1. ``svd-hf`` — Hugging Face Space ``multimodalart/stable-video-diffusion``
2. ``wan-hf`` — Hugging Face Space ``Upsampler/wan-2-2-14b-image-to-video``
3. ``svd-local`` — local ``stabilityai/stable-video-diffusion-img2vid``
   (``.venv-i2v311``; CPU only on Intel Mac — MPS lacks Conv3D)

Optical-flow / parallax still-warps are **disabled** as a default. Pass
``--allow-warp-fallback`` only for local debugging; do not ship those assets.

Examples::

    # Prefer cloud I2V, then encode MP4 + GIF:
    .venv/bin/python scripts/generate_demo_videos.py --backend auto

    # Encode existing generative MP4s under docs/media/video_raw/:
    .venv/bin/python scripts/generate_demo_videos.py --backend encode

    # Force Wan Space I2V:
    .venv/bin/python scripts/generate_demo_videos.py --backend wan-hf --only tidy
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "media"
FRAMES = OUT / "frames"
VIDEO_RAW = OUT / "video_raw"
META = OUT / "_i2v_meta"
SIZE = (720, 404)
DURATION_S = 5.0
FPS = 16

SCENES = {
    "navigate": {
        "stem": "demo-navigate",
        "seed": FRAMES / "navigate" / "02.png",
        "mp4_raw": VIDEO_RAW / "navigate.mp4",
        "prompt": (
            "NestWeaver white home robot with pill head, two black camera eyes, teal LEDs, "
            "mecanum wheels driving through a bright living room past a sofa, continuous motion"
        ),
        "motion": 200,
    },
    "pick": {
        "stem": "demo-pick-bottle",
        "seed": FRAMES / "pick" / "03.png",
        "mp4_raw": VIDEO_RAW / "pick.mp4",
        "prompt": (
            "NestWeaver robot extending articulated arm and grasping a clear water bottle "
            "from a side table, continuous cinematic motion"
        ),
        "motion": 200,
    },
    "deliver": {
        "stem": "demo-deliver",
        "seed": FRAMES / "deliver" / "03.png",
        "mp4_raw": VIDEO_RAW / "deliver.mp4",
        "prompt": (
            "NestWeaver home robot driving across living room and handing water bottle "
            "to person on sofa, continuous motion"
        ),
        "motion": 190,
    },
    "voice": {
        "stem": "demo-voice-llm",
        "seed": FRAMES / "voice" / "02.png",
        "mp4_raw": VIDEO_RAW / "voice.mp4",
        "prompt": (
            "NestWeaver white home robot rolling through living room while teal LED ring "
            "pulses as if speaking, continuous locomotion"
        ),
        "motion": 170,
    },
    "tidy": {
        "stem": "demo-tidy",
        "seed": FRAMES / "tidy" / "03.png",
        "mp4_raw": VIDEO_RAW / "tidy.mp4",
        "prompt": (
            "NestWeaver robot picking a toy from hardwood floor into a wicker basket, "
            "base repositioning, continuous motion"
        ),
        "motion": 190,
    },
}


def _ffmpeg() -> str:
    ff = shutil.which("ffmpeg")
    if not ff:
        raise SystemExit("ffmpeg is required on PATH")
    return ff


def _seed(scene: str) -> Path:
    seed = SCENES[scene]["seed"]
    if seed.exists():
        return seed
    alts = sorted((FRAMES / scene).glob("*.png"))
    if not alts:
        raise SystemExit(f"No seed frames for {scene}")
    return alts[0]


def _write_meta(scene: str, payload: dict) -> None:
    META.mkdir(parents=True, exist_ok=True)
    (META / f"{scene}.json").write_text(json.dumps(payload, indent=2))


def run_svd_hf(seed: Path, dest: Path, motion: int = 180) -> dict:
    from gradio_client import Client, handle_file

    client = Client("multimodalart/stable-video-diffusion")
    result = client.predict(
        handle_file(str(seed)),
        abs(hash(seed.name)) % 10_000_000,
        False,
        motion,
        5,
        api_name="/video",
    )
    video = result[0]
    path = video["video"] if isinstance(video, dict) else video
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(path, dest)
    return {"model": "multimodalart/stable-video-diffusion (SVD img2vid)", "path": str(dest)}


def run_wan_hf(seed: Path, dest: Path, prompt: str, duration: float = 3.5, steps: int = 4) -> dict:
    from gradio_client import Client, handle_file

    client = Client("Upsampler/wan-2-2-14b-image-to-video")
    result = client.predict(
        handle_file(str(seed)),
        prompt,
        steps,
        "static, still image, blurry, low quality, watermark, text",
        duration,
        1.0,
        1.0,
        abs(hash(str(seed))) % 100_000,
        False,
        None,
        api_name="/generate_video",
    )
    video = result[0]
    path = video["video"] if isinstance(video, dict) else video
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(path, dest)
    return {
        "model": "Upsampler/wan-2-2-14b-image-to-video",
        "path": str(dest),
        "duration_seconds": duration,
        "steps": steps,
    }


def run_svd_local(seed: Path, dest: Path, motion: int = 180) -> dict:
    import torch
    from diffusers import StableVideoDiffusionPipeline
    from diffusers.utils import export_to_video, load_image

    pipe = StableVideoDiffusionPipeline.from_pretrained(
        "stabilityai/stable-video-diffusion-img2vid",
        torch_dtype=torch.float32,
        variant="fp16",
    )
    pipe.to("cpu")
    pipe.enable_attention_slicing()
    image = load_image(str(seed)).resize((512, 288))
    frames = pipe(
        image,
        decode_chunk_size=1,
        motion_bucket_id=motion,
        noise_aug_strength=0.02,
        num_frames=8,
        num_inference_steps=6,
    ).frames[0]
    dest.parent.mkdir(parents=True, exist_ok=True)
    export_to_video(frames, str(dest), fps=5)
    return {
        "model": "stabilityai/stable-video-diffusion-img2vid (local CPU)",
        "path": str(dest),
        "num_frames": 8,
        "num_inference_steps": 6,
    }


def encode_outputs(src: Path, stem: str) -> dict:
    """Encode GitHub-friendly MP4 + GIF from a generative source clip."""
    ff = _ffmpeg()
    mp4_out = OUT / f"{stem}.mp4"
    gif_out = OUT / f"{stem}.gif"
    OUT.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="nwvid_") as tmp:
        tmp_path = Path(tmp)
        smooth = tmp_path / "smooth.mp4"
        vf = (
            f"minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
            f"scale={SIZE[0]}:{SIZE[1]}:flags=lanczos,fps={FPS}"
        )
        subprocess.run(
            [
                ff, "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(src), "-vf", vf, "-an", "-pix_fmt", "yuv420p", str(smooth),
            ],
            check=True,
        )
        probe = subprocess.run(
            [
                shutil.which("ffprobe") or "ffprobe",
                "-v", "error", "-show_entries", "format=duration",
                "-of", "default=nw=1:nk=1", str(smooth),
            ],
            check=True, capture_output=True, text=True,
        )
        try:
            dur = float(probe.stdout.strip())
        except ValueError:
            dur = DURATION_S
        final = smooth
        if abs(dur - DURATION_S) > 0.05:
            stretched = tmp_path / "stretched.mp4"
            factor = DURATION_S / max(dur, 0.01)
            subprocess.run(
                [
                    ff, "-y", "-hide_banner", "-loglevel", "error",
                    "-i", str(smooth),
                    "-filter:v", f"setpts=PTS*{factor:.6f},fps={FPS}",
                    "-t", str(DURATION_S), "-an", "-pix_fmt", "yuv420p",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "20",
                    str(stretched),
                ],
                check=True,
            )
            final = stretched
        else:
            subprocess.run(
                [
                    ff, "-y", "-hide_banner", "-loglevel", "error",
                    "-i", str(smooth), "-t", str(DURATION_S),
                    "-an", "-pix_fmt", "yuv420p",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "20",
                    str(mp4_out),
                ],
                check=True,
            )
            final = mp4_out

        if final != mp4_out:
            shutil.copy(final, mp4_out)

        palette = tmp_path / "palette.png"
        subprocess.run(
            [
                ff, "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(mp4_out),
                "-vf", f"fps={FPS},palettegen=stats_mode=diff",
                str(palette),
            ],
            check=True,
        )
        subprocess.run(
            [
                ff, "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(mp4_out), "-i", str(palette),
                "-lavfi",
                f"fps={FPS}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle",
                str(gif_out),
            ],
            check=True,
        )

    return {
        "mp4": mp4_out.name,
        "gif": gif_out.name,
        "mp4_mb": round(mp4_out.stat().st_size / (1024 * 1024), 2),
        "gif_mb": round(gif_out.stat().st_size / (1024 * 1024), 2),
    }


def generate_raw(scene: str, backend: str) -> dict:
    meta = SCENES[scene]
    seed = _seed(scene)
    dest = meta["mp4_raw"]

    if backend == "encode":
        if not dest.exists():
            raise SystemExit(f"Missing generative source {dest}")
        return {"model": f"existing:{dest.name}", "path": str(dest), "kept": True}

    if backend == "svd-hf":
        info = run_svd_hf(seed, dest, meta["motion"])
    elif backend == "wan-hf":
        info = run_wan_hf(seed, dest, meta["prompt"])
    elif backend == "svd-local":
        info = run_svd_local(seed, dest, meta["motion"])
    elif backend == "auto":
        errors: list[str] = []
        if dest.exists() and dest.stat().st_size > 100_000:
            return {"model": f"existing:{dest.name}", "path": str(dest), "kept": True}
        for name, fn in (
            ("svd-hf", lambda: run_svd_hf(seed, dest, meta["motion"])),
            ("wan-hf", lambda: run_wan_hf(seed, dest, meta["prompt"])),
            ("svd-local", lambda: run_svd_local(seed, dest, meta["motion"])),
        ):
            try:
                print(f"  trying {name} ...", flush=True)
                info = fn()
                info["backend"] = name
                return info
            except Exception as exc:  # noqa: BLE001 — try next backend
                errors.append(f"{name}: {exc}")
                print(f"  {name} failed: {exc}", flush=True)
        raise SystemExit(
            "All generative I2V backends failed (warp fallback disabled).\n"
            + "\n".join(errors)
        )
    else:
        raise SystemExit(f"Unknown backend {backend}")

    return info


def build_scene(scene: str, backend: str) -> dict:
    print(f"=== {scene} ===", flush=True)
    gen = generate_raw(scene, backend)
    enc = encode_outputs(Path(gen["path"]), SCENES[scene]["stem"])
    payload = {
        "scene": scene,
        **gen,
        **enc,
        "duration_s": DURATION_S,
        "fps": FPS,
    }
    _write_meta(scene, payload)
    print(
        f"{enc['mp4']} / {enc['gif']}: {payload.get('model')} → "
        f"~{DURATION_S}s @ {FPS}fps, mp4={enc['mp4_mb']}MB gif={enc['gif_mb']}MB",
        flush=True,
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backend",
        choices=["auto", "svd-hf", "wan-hf", "svd-local", "encode"],
        default="auto",
        help="I2V backend (auto tries HF SVD → Wan → local; encode uses existing raw MP4s)",
    )
    parser.add_argument("--only", nargs="*", default=None, help="Subset of scenes")
    parser.add_argument(
        "--allow-warp-fallback",
        action="store_true",
        help="DEPRECATED: refused. Optical-flow warps must not ship as demos.",
    )
    args = parser.parse_args()
    if args.allow_warp_fallback:
        raise SystemExit(
            "Warp/parallax fallback is hard-disabled. Obtain I2V API access "
            "(HF token / Replicate / fal) or use --backend svd-local."
        )

    OUT.mkdir(parents=True, exist_ok=True)
    VIDEO_RAW.mkdir(parents=True, exist_ok=True)
    scenes = args.only or list(SCENES.keys())
    results = []
    for scene in scenes:
        if scene not in SCENES:
            raise SystemExit(f"Unknown scene {scene}")
        results.append(build_scene(scene, args.backend))
    print("Done. Outputs in", OUT)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
