#!/usr/bin/env python3
"""LEGACY wrapper — prefer ``scripts/generate_demo_videos.py``.

This script can still encode GIFs from generative I2V MP4s under
``docs/media/video_raw/``. Optical-flow / parallax still-warps are **not** used
by default and must not be shipped as README demos.

For the real I2V pipeline (SVD / Wan / local) + MP4+GIF outputs, run::

    .venv/bin/python scripts/generate_demo_videos.py --backend auto
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

try:
    from PIL import Image  # noqa: F401  # dependency check / optional pillow path
except ImportError as exc:
    raise SystemExit("Pillow required: pip install Pillow\n" + str(exc)) from exc

try:
    import cv2
except ImportError as exc:
    raise SystemExit(
        "opencv-python required: pip install opencv-python-headless\n" + str(exc)
    ) from exc

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "media"
FRAMES = OUT / "frames"
VIDEO_RAW = OUT / "video_raw"
SIZE = (720, 404)  # even dims for encoders
DURATION_S = 5.0
FPS = 16
N_FRAMES = int(DURATION_S * FPS)

SCENES = {
    "navigate": {
        "gif": "demo-navigate.gif",
        "seed": FRAMES / "navigate" / "02.png",
        "mp4": VIDEO_RAW / "navigate.mp4",
        "drive": (2.2, 0.12),
        "arm_target": None,
        "arm_strength": 0.0,
    },
    "pick": {
        "gif": "demo-pick-bottle.gif",
        "seed": FRAMES / "pick" / "03.png",
        "mp4": VIDEO_RAW / "pick.mp4",
        "drive": (2.0, 0.12),
        "arm_target": (0.28, 0.62),
        "arm_strength": 0.6,
    },
    "deliver": {
        "gif": "demo-deliver.gif",
        "seed": FRAMES / "deliver" / "03.png",
        "mp4": VIDEO_RAW / "deliver.mp4",
        "drive": (2.4, 0.05),
        "arm_target": (0.62, 0.48),
        "arm_strength": 0.4,
    },
    "voice": {
        "gif": "demo-voice-llm.gif",
        "seed": FRAMES / "voice" / "02.png",
        "mp4": VIDEO_RAW / "voice.mp4",
        "drive": (1.8, 0.1),
        "arm_target": None,
        "arm_strength": 0.0,
    },
    "tidy": {
        "gif": "demo-tidy.gif",
        "seed": FRAMES / "tidy" / "03.png",
        "mp4": VIDEO_RAW / "tidy.mp4",
        "drive": (1.6, 0.18),
        "arm_target": (0.35, 0.72),
        "arm_strength": 0.55,
    },
}


def _ffmpeg() -> str:
    ff = shutil.which("ffmpeg")
    if not ff:
        raise SystemExit("ffmpeg is required on PATH")
    return ff


def _seed_for(scene: str) -> Path:
    meta = SCENES[scene]
    seed = meta["seed"]
    if seed.exists():
        return seed
    alts = sorted((FRAMES / scene).glob("*.png"))
    if not alts:
        raise SystemExit(f"No seed frames for {scene}")
    return alts[0]


# ----- continuous parallax-flow synthesis (not crossfade) --------------------

def _parallax_flow(h: int, w: int, drive_dx: float, drive_dy: float) -> np.ndarray:
    yy, xx = np.indices((h, w), dtype=np.float32)
    v = (yy / max(h - 1, 1)) ** 1.35
    flow = np.zeros((h, w, 2), np.float32)
    flow[..., 0] = drive_dx * (0.25 + 0.75 * v)
    flow[..., 1] = drive_dy * (0.35 + 0.65 * v)
    curve = 0.35 * np.sin((xx / w) * np.pi) * v
    flow[..., 1] += curve * abs(drive_dx) * 0.15
    return flow


def _arm_flow(
    h: int, w: int, target_nx: float, target_ny: float, strength: float
) -> np.ndarray:
    yy, xx = np.indices((h, w), dtype=np.float32)
    tx, ty = target_nx * w, target_ny * h
    mask = (
        (xx >= 0.35 * w) & (xx <= 0.72 * w) & (yy >= 0.20 * h) & (yy <= 0.78 * h)
    ).astype(np.float32)
    mask = cv2.GaussianBlur(mask, (0, 0), 18)
    flow = np.zeros((h, w, 2), np.float32)
    flow[..., 0] = ((tx - xx) / w) * strength * 28 * mask
    flow[..., 1] = ((ty - yy) / h) * strength * 28 * mask
    return flow


def _warp(img: np.ndarray, flow: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    yy, xx = np.indices((h, w), dtype=np.float32)
    map_x = np.ascontiguousarray(xx + flow[..., 0], dtype=np.float32)
    map_y = np.ascontiguousarray(yy + flow[..., 1], dtype=np.float32)
    return cv2.remap(
        img, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101
    )


def _pulse_teal(img: np.ndarray, amount: float) -> np.ndarray:
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    led = ((h > 80) & (h < 110) & (s > 40) & (v > 60)).astype(np.float32)
    led = cv2.GaussianBlur(led, (0, 0), 3)
    s2 = np.clip(s.astype(np.float32) + led * amount * 25, 0, 255).astype(np.uint8)
    v2 = np.clip(v.astype(np.float32) + led * amount * 40, 0, 255).astype(np.uint8)
    return cv2.cvtColor(cv2.merge([h, s2, v2]), cv2.COLOR_HSV2BGR)


def synthesize_flow(scene: str) -> list[np.ndarray]:
    meta = SCENES[scene]
    seed = _seed_for(scene)
    img = cv2.resize(cv2.imread(str(seed)), SIZE, interpolation=cv2.INTER_AREA)
    h, w = img.shape[:2]
    base = _parallax_flow(h, w, *meta["drive"])
    arm = None
    if meta["arm_target"] and meta["arm_strength"] > 0:
        arm = _arm_flow(h, w, *meta["arm_target"], meta["arm_strength"])

    frames: list[np.ndarray] = []
    for i in range(N_FRAMES):
        t = i / (N_FRAMES - 1)
        te = t * t * (3 - 2 * t)
        flow = base * (i * 0.9)
        if arm is not None:
            flow = flow + arm * float(np.sin(te * np.pi))
        fr = _warp(img, flow.astype(np.float32))
        bob = int(2 * np.sin(t * 2 * np.pi * 1.5))
        if bob:
            fr = np.roll(fr, bob, axis=0)
        fr = _pulse_teal(fr, 0.35 + 0.65 * (0.5 + 0.5 * np.sin(t * 2 * np.pi * 3)))
        if i % 2 == 0:
            fr = cv2.GaussianBlur(fr, (3, 1), 0)
        frames.append(fr)
    return frames


# ----- optical-flow between keyframes (no alpha crossfade) -------------------

def _of_interp(a: np.ndarray, b: np.ndarray, n: int) -> list[np.ndarray]:
    a_g = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
    b_g = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)
    flow_ab = cv2.calcOpticalFlowFarneback(a_g, b_g, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    flow_ba = cv2.calcOpticalFlowFarneback(b_g, a_g, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    h, w = a_g.shape
    yy, xx = np.indices((h, w), dtype=np.float32)
    out: list[np.ndarray] = []
    for i in range(n):
        t = i / max(n, 1)
        t = t * t * (3 - 2 * t)
        mx = np.ascontiguousarray(xx + flow_ab[..., 0] * t, dtype=np.float32)
        my = np.ascontiguousarray(yy + flow_ab[..., 1] * t, dtype=np.float32)
        wa = cv2.remap(a, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        mx2 = np.ascontiguousarray(xx + flow_ba[..., 0] * (1 - t), dtype=np.float32)
        my2 = np.ascontiguousarray(yy + flow_ba[..., 1] * (1 - t), dtype=np.float32)
        wb = cv2.remap(b, mx2, my2, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        out.append(cv2.addWeighted(wa, 1 - t, wb, t, 0))
    return out


def synthesize_of_keys(scene: str) -> list[np.ndarray]:
    paths = sorted((FRAMES / scene).glob("*.png"))
    if len(paths) < 2:
        raise SystemExit(f"Need >=2 keyframes in {FRAMES / scene}")
    keys = [cv2.resize(cv2.imread(str(p)), SIZE) for p in paths]
    gaps = len(keys) - 1
    base = N_FRAMES // gaps
    rem = N_FRAMES % gaps
    seq: list[np.ndarray] = []
    for g in range(gaps):
        steps = base + (1 if g < rem else 0)
        seq.extend(_of_interp(keys[g], keys[g + 1], steps))
    return seq[:N_FRAMES]


# ----- encoders --------------------------------------------------------------

def encode_gif_frames(frames: list[np.ndarray], dest: Path, fps: int = FPS) -> None:
    ff = _ffmpeg()
    with tempfile.TemporaryDirectory(prefix="nwgif_") as tmp:
        tmp_path = Path(tmp)
        for i, fr in enumerate(frames):
            cv2.imwrite(str(tmp_path / f"f{i:04d}.png"), fr)
        pattern = str(tmp_path / "f%04d.png")
        palette = tmp_path / "palette.png"
        subprocess.run(
            [
                ff, "-y", "-hide_banner", "-loglevel", "error",
                "-framerate", str(fps), "-i", pattern,
                "-vf", "palettegen=stats_mode=diff", str(palette),
            ],
            check=True,
        )
        subprocess.run(
            [
                ff, "-y", "-hide_banner", "-loglevel", "error",
                "-framerate", str(fps), "-i", pattern, "-i", str(palette),
                "-lavfi",
                "paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle",
                str(dest),
            ],
            check=True,
        )


def encode_gif_from_mp4(src: Path, dest: Path, fps: int = FPS, duration: float = DURATION_S) -> None:
    ff = _ffmpeg()
    with tempfile.TemporaryDirectory(prefix="nwvid_") as tmp:
        tmp_path = Path(tmp)
        smooth = tmp_path / "smooth.mp4"
        vf = (
            f"minterpolate=fps={fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
            f"scale={SIZE[0]}:{SIZE[1]}:flags=lanczos,fps={fps}"
        )
        subprocess.run(
            [
                ff, "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(src), "-vf", vf, "-t", str(duration),
                "-an", "-pix_fmt", "yuv420p", str(smooth),
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
            dur = duration
        final = smooth
        if dur < duration - 0.05:
            stretched = tmp_path / "stretched.mp4"
            factor = duration / max(dur, 0.01)
            subprocess.run(
                [
                    ff, "-y", "-hide_banner", "-loglevel", "error",
                    "-i", str(smooth),
                    "-filter:v", f"setpts=PTS*{factor:.6f},fps={fps}",
                    "-t", str(duration), "-an", "-pix_fmt", "yuv420p", str(stretched),
                ],
                check=True,
            )
            final = stretched
        palette = tmp_path / "palette.png"
        subprocess.run(
            [
                ff, "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(final), "-vf", f"fps={fps},palettegen=stats_mode=diff",
                str(palette),
            ],
            check=True,
        )
        subprocess.run(
            [
                ff, "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(final), "-i", str(palette),
                "-lavfi",
                f"fps={fps}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle",
                str(dest),
            ],
            check=True,
        )


def run_svd_local(seed: Path, dest_mp4: Path, motion: int = 180, num_frames: int = 14) -> None:
    import torch
    from diffusers import StableVideoDiffusionPipeline
    from diffusers.utils import load_image, export_to_video

    print(f"  SVD-local: loading pipeline for {seed.name} ...", flush=True)
    try:
        pipe = StableVideoDiffusionPipeline.from_pretrained(
            "stabilityai/stable-video-diffusion-img2vid",
            torch_dtype=torch.float32,
            variant="fp16",
        )
    except Exception:
        pipe = StableVideoDiffusionPipeline.from_pretrained(
            "stabilityai/stable-video-diffusion-img2vid",
            torch_dtype=torch.float32,
        )
    pipe = pipe.to("cpu")
    image = load_image(str(seed)).resize((1024, 576))
    print(f"  SVD-local: generating {num_frames} frames (CPU, slow) ...", flush=True)
    frames = pipe(
        image,
        decode_chunk_size=1,
        motion_bucket_id=motion,
        noise_aug_strength=0.02,
        num_frames=num_frames,
        num_inference_steps=18,
    ).frames[0]
    dest_mp4.parent.mkdir(parents=True, exist_ok=True)
    export_to_video(frames, str(dest_mp4), fps=6)


def run_svd_hf_space(seed: Path, dest_mp4: Path, motion: int = 180) -> None:
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
    dest_mp4.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(path, dest_mp4)


def build_scene(scene: str, method: str) -> dict:
    meta = SCENES[scene]
    dest = OUT / meta["gif"]
    mp4 = meta["mp4"]
    seed = _seed_for(scene)
    used = None

    if method == "encode" and mp4.exists():
        encode_gif_from_mp4(mp4, dest)
        used = f"i2v-mp4:{mp4.name}"
    elif method == "svd-local":
        run_svd_local(seed, mp4)
        encode_gif_from_mp4(mp4, dest)
        used = "svd-local"
    elif method == "svd-hf":
        run_svd_hf_space(seed, mp4)
        encode_gif_from_mp4(mp4, dest)
        used = "svd-hf"
    elif method in ("flow", "of"):
        raise SystemExit(
            f"method={method} is hard-disabled (still-warp demos must not ship). "
            "Use scripts/generate_demo_videos.py for true I2V."
        )
    elif method == "auto":
        if mp4.exists() and mp4.stat().st_size > 20_000:
            encode_gif_from_mp4(mp4, dest)
            used = f"mp4:{mp4.name}"
        else:
            try:
                run_svd_hf_space(seed, mp4)
                encode_gif_from_mp4(mp4, dest)
                used = "svd-hf"
            except Exception as exc:
                raise SystemExit(
                    f"HF I2V unavailable ({exc}). Warp fallback is disabled. "
                    "Set HF_TOKEN / use Wan Space / run --method svd-local, "
                    "or prefer scripts/generate_demo_videos.py."
                ) from exc
    else:
        raise SystemExit(f"Unknown method {method}")

    size_mb = dest.stat().st_size / (1024 * 1024)
    return {
        "scene": scene,
        "file": dest.name,
        "method": used,
        "size_mb": round(size_mb, 2),
        "duration_s": DURATION_S,
        "fps": FPS,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--method",
        choices=["auto", "flow", "of", "svd-local", "svd-hf", "encode"],
        default="auto",
    )
    parser.add_argument("--only", nargs="*", default=None)
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    VIDEO_RAW.mkdir(parents=True, exist_ok=True)
    scenes = args.only or list(SCENES.keys())
    for scene in scenes:
        if scene not in SCENES:
            raise SystemExit(f"Unknown scene {scene}")
        print(f"=== {scene} ===", flush=True)
        info = build_scene(scene, args.method)
        print(
            f"{info['file']}: {info['method']} → ~{info['duration_s']}s @ {info['fps']}fps, "
            f"{info['size_mb']} MB",
            flush=True,
        )
    print("Done. GIFs written to", OUT)


if __name__ == "__main__":
    main()
