#!/usr/bin/env python3
"""Generate five realistic-looking home-robot demo GIFs for the README.

These are *simulated demo visualizations* — not real robot footage. They are
synthesized with Pillow so the repository renders rich media on GitHub without
binary camera captures.

Usage:
  python scripts/generate_demo_gifs.py
  # or:  .venv/bin/python scripts/generate_demo_gifs.py
"""

from __future__ import annotations

import math
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except ImportError as exc:
    raise SystemExit(
        "Pillow is required. Install with: pip install Pillow\n" + str(exc)
    ) from exc

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "media"
W, H = 640, 360


def _font(size: int):
    for name in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


FONT_SM = _font(14)
FONT_MD = _font(18)
FONT_LG = _font(22)


def _living_room_bg(frame: int, n: int) -> Image.Image:
    """Warm living-room-ish backdrop with floor, sofa, rug, window light."""
    img = Image.new("RGB", (W, H), (42, 38, 36))
    d = ImageDraw.Draw(img)
    # Floor
    d.rectangle([0, 200, W, H], fill=(92, 70, 52))
    # Floor planks
    for x in range(0, W, 40):
        d.line([(x, 200), (x + 30, H)], fill=(78, 58, 42), width=1)
    # Back wall
    d.rectangle([0, 0, W, 200], fill=(210, 200, 188))
    # Window light wash
    d.rectangle([420, 30, 600, 160], fill=(235, 228, 210))
    d.rectangle([430, 40, 590, 150], fill=(180, 210, 230))
    # Sofa
    d.rounded_rectangle([40, 120, 280, 210], radius=12, fill=(70, 90, 110))
    d.rounded_rectangle([50, 100, 150, 140], radius=8, fill=(60, 78, 95))
    d.rounded_rectangle([170, 100, 270, 140], radius=8, fill=(60, 78, 95))
    # Rug
    d.ellipse([180, 250, 480, 330], fill=(140, 70, 60))
    d.ellipse([200, 260, 460, 320], fill=(160, 90, 75))
    # Coffee table
    d.rounded_rectangle([250, 230, 400, 270], radius=4, fill=(120, 95, 70))
    # Soft vignette
    vig = Image.new("RGB", (W, H), (0, 0, 0))
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-40, -40, W + 40, H + 40], fill=(255, 255, 255))
    vig = vig.filter(ImageFilter.GaussianBlur(40))
    img = Image.composite(img, Image.new("RGB", (W, H), (20, 18, 16)), vig.convert("L"))
    # Subtle film grain via noise-ish dither of brightness by frame
    return img


def _draw_robot(d: ImageDraw.ImageDraw, x: float, y: float, yaw: float, arm_phase: float = 0.0):
    """Draw a compact omni-base + mast + arm silhouette."""
    # Shadow
    d.ellipse([x - 28, y + 8, x + 28, y + 22], fill=(40, 30, 25, 128) if False else (55, 42, 35))
    # Base (rounded)
    d.rounded_rectangle([x - 26, y - 12, x + 26, y + 12], radius=8, fill=(35, 38, 42))
    # Mecanum wheel hints
    for wx in (-18, 18):
        d.ellipse([x + wx - 6, y + 2, x + wx + 6, y + 14], fill=(20, 20, 22))
    # Body column
    d.rounded_rectangle([x - 12, y - 55, x + 12, y - 10], radius=4, fill=(55, 120, 130))
    # Status LED
    led = (80, 220, 140) if arm_phase < 0.7 else (240, 200, 80)
    d.ellipse([x - 4, y - 48, x + 4, y - 40], fill=led)
    # Camera mast
    d.rectangle([x - 2, y - 85, x + 2, y - 55], fill=(70, 75, 80))
    d.rounded_rectangle([x - 14, y - 98, x + 14, y - 82], radius=3, fill=(30, 32, 36))
    d.rectangle([x - 8, y - 94, x + 8, y - 86], fill=(100, 160, 200))
    # Arm (6-DoF stylized)
    shoulder = (x + 10, y - 50)
    elbow_x = shoulder[0] + 28 * math.cos(yaw + arm_phase)
    elbow_y = shoulder[1] + 22 * math.sin(arm_phase - 0.3)
    wrist_x = elbow_x + 22 * math.cos(yaw + arm_phase + 0.4)
    wrist_y = elbow_y + 10 * math.sin(arm_phase)
    d.line([shoulder, (elbow_x, elbow_y)], fill=(200, 200, 205), width=5)
    d.line([(elbow_x, elbow_y), (wrist_x, wrist_y)], fill=(180, 185, 190), width=4)
    d.ellipse([wrist_x - 5, wrist_y - 5, wrist_x + 5, wrist_y + 5], fill=(230, 230, 235))
    return wrist_x, wrist_y


def _caption(img: Image.Image, title: str, subtitle: str) -> Image.Image:
    d = ImageDraw.Draw(img)
    d.rectangle([0, H - 42, W, H], fill=(18, 18, 20))
    d.text((12, H - 38), title, fill=(240, 240, 242), font=FONT_MD)
    d.text((12, H - 18), subtitle, fill=(160, 165, 170), font=FONT_SM)
    # Banner
    d.rectangle([0, 0, W, 22], fill=(18, 18, 20))
    d.text((10, 3), "NestWeaver · simulated demo visualization", fill=(140, 200, 190), font=FONT_SM)
    return img


def _save_gif(frames: list[Image.Image], path: Path, duration: int = 80) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
        optimize=True,
    )
    print(f"Wrote {path} ({len(frames)} frames, {path.stat().st_size // 1024} KB)")


def gif_navigate() -> None:
    frames = []
    n = 24
    for i in range(n):
        img = _living_room_bg(i, n)
        d = ImageDraw.Draw(img)
        # SLAM path
        pts = []
        for t in range(i + 1):
            u = t / max(n - 1, 1)
            px = 80 + u * 360
            py = 280 - 30 * math.sin(u * math.pi)
            pts.append((px, py))
            # obstacle markers
        d.ellipse([330, 255, 360, 285], fill=(90, 90, 95))  # chair leg / obstacle
        if len(pts) > 1:
            d.line(pts, fill=(80, 200, 160), width=3)
        # planned path dashed ahead
        for t in range(i, n):
            u = t / max(n - 1, 1)
            px = 80 + u * 360
            py = 280 - 30 * math.sin(u * math.pi)
            if t % 2 == 0:
                d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(80, 200, 160))
        u = i / max(n - 1, 1)
        rx = 80 + u * 360
        ry = 280 - 30 * math.sin(u * math.pi)
        # Avoid obstacle bump in path
        if 0.45 < u < 0.6:
            ry -= 25
        _draw_robot(d, rx, ry, yaw=0.1 * math.sin(i / 3), arm_phase=0.2)
        _caption(img, "1 · Navigating living room", "Obstacle-aware path · local SLAM (simulated)")
        frames.append(img)
    _save_gif(frames, OUT / "demo-navigate.gif")


def gif_pick_bottle() -> None:
    frames = []
    n = 24
    for i in range(n):
        img = _living_room_bg(i, n)
        d = ImageDraw.Draw(img)
        # Bottle on table
        bx, by = 320, 220
        d.rounded_rectangle([bx - 8, by - 35, bx + 8, by + 5], radius=3, fill=(40, 140, 210))
        d.ellipse([bx - 8, by - 40, bx + 8, by - 30], fill=(90, 180, 230))
        phase = min(1.0, i / (n * 0.7))
        rx, ry = 260, 290
        wrist = _draw_robot(d, rx, ry, yaw=0.2, arm_phase=0.3 + phase * 1.1)
        if phase > 0.55:
            # Bottle moves with gripper
            gx, gy = wrist
            d.rounded_rectangle([gx - 6, gy - 20, gx + 6, gy + 5], radius=2, fill=(40, 140, 210))
            # Clear table bottle
            d.rounded_rectangle([bx - 8, by - 35, bx + 8, by + 5], radius=3, fill=(120, 95, 70))
        # Depth overlay hint
        d.rectangle([12, 30, 120, 100], outline=(80, 200, 160), width=1)
        d.text((18, 34), "depth ROI", fill=(80, 200, 160), font=FONT_SM)
        _caption(img, "2 · Picking up a water bottle", "Depth grasp · 6-DoF arm (simulated)")
        frames.append(img)
    _save_gif(frames, OUT / "demo-pick-bottle.gif")


def gif_deliver() -> None:
    frames = []
    n = 24
    for i in range(n):
        img = _living_room_bg(i, n)
        d = ImageDraw.Draw(img)
        # Person silhouette near sofa
        d.ellipse([95, 95, 125, 125], fill=(200, 170, 150))
        d.rounded_rectangle([90, 125, 130, 200], radius=8, fill=(50, 70, 90))
        u = i / max(n - 1, 1)
        rx = 420 - u * 250
        ry = 300 - 10 * math.sin(u * math.pi)
        phase = 0.9 if u < 0.75 else 0.9 - (u - 0.75) * 2
        wrist = _draw_robot(d, rx, ry, yaw=-0.4, arm_phase=phase)
        if u < 0.8:
            gx, gy = wrist
            d.rounded_rectangle([gx - 6, gy - 18, gx + 6, gy + 4], radius=2, fill=(40, 140, 210))
        else:
            # Placed on table
            d.rounded_rectangle([300, 210, 316, 245], radius=2, fill=(40, 140, 210))
        _caption(img, "3 · Delivering bottle to person", "Fetch-and-carry handover (simulated)")
        frames.append(img)
    _save_gif(frames, OUT / "demo-deliver.gif")


def gif_voice() -> None:
    frames = []
    n = 24
    for i in range(n):
        img = _living_room_bg(i, n)
        d = ImageDraw.Draw(img)
        u = i / max(n - 1, 1)
        rx = 120 + u * 300
        ry = 290
        _draw_robot(d, rx, ry, yaw=0.05, arm_phase=0.25)
        # Voice waveform + LLM chip
        cx, cy = int(rx), int(ry - 110)
        amp = 8 + 6 * math.sin(i * 0.8)
        for k in range(8):
            h = amp * (0.5 + 0.5 * math.sin(i * 0.5 + k))
            d.rectangle([cx - 40 + k * 10, cy - h, cx - 34 + k * 10, cy + h], fill=(100, 220, 180))
        d.rounded_rectangle([W - 210, 40, W - 16, 110], radius=8, fill=(24, 28, 30))
        d.text((W - 198, 48), "Local LLM · Ollama", fill=(140, 220, 190), font=FONT_SM)
        d.text((W - 198, 70), "“Where is my bottle?”", fill=(230, 230, 230), font=FONT_SM)
        ans = "On the coffee table."[: max(1, (i * 2) % 22)]
        d.text((W - 198, 90), ans, fill=(180, 190, 200), font=FONT_SM)
        _caption(img, "4 · Voice query while moving", "On-device Ollama · no cloud (simulated)")
        frames.append(img)
    _save_gif(frames, OUT / "demo-voice-llm.gif")


def gif_tidy() -> None:
    frames = []
    n = 24
    for i in range(n):
        img = _living_room_bg(i, n)
        d = ImageDraw.Draw(img)
        # Shelf on right
        d.rectangle([520, 100, 620, 220], fill=(110, 90, 70))
        d.line([(520, 140), (620, 140)], fill=(90, 70, 55), width=3)
        d.line([(520, 180), (620, 180)], fill=(90, 70, 55), width=3)
        # Toy on floor then moved
        u = i / max(n - 1, 1)
        if u < 0.35:
            d.ellipse([300, 300, 330, 325], fill=(220, 120, 60))
            rx, ry = 250, 300
            phase = 0.4 + u * 2
            wrist = _draw_robot(d, rx, ry, yaw=0.3, arm_phase=phase)
        elif u < 0.75:
            rx = 250 + (u - 0.35) / 0.4 * 280
            ry = 300 - 20
            wrist = _draw_robot(d, rx, ry, yaw=0.1, arm_phase=1.0)
            gx, gy = wrist
            d.ellipse([gx - 12, gy - 8, gx + 12, gy + 10], fill=(220, 120, 60))
        else:
            rx, ry = 530, 280
            _draw_robot(d, rx, ry, yaw=0.0, arm_phase=0.5)
            d.ellipse([545, 150, 575, 175], fill=(220, 120, 60))
        _caption(img, "5 · Tidying — putting an item away", "Clutter → shelf behavior (simulated)")
        frames.append(img)
    _save_gif(frames, OUT / "demo-tidy.gif")


def write_captions_md() -> None:
    text = """# Demo media captions

All GIFs are **simulated demo visualizations** generated by
`scripts/generate_demo_gifs.py`. They are not real robot camera footage.

| File | Scene |
|------|--------|
| `demo-navigate.gif` | Omnibase navigating a living room with obstacle-aware path |
| `demo-pick-bottle.gif` | 6-DoF arm picking a water bottle using depth ROI |
| `demo-deliver.gif` | Fetch-and-carry delivery to a person / table |
| `demo-voice-llm.gif` | Voice query answered by local Ollama while moving |
| `demo-tidy.gif` | Tidying behavior — clutter item returned to a shelf |

Regenerate:

```bash
python scripts/generate_demo_gifs.py
```
"""
    (OUT / "README.md").write_text(text)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    gif_navigate()
    gif_pick_bottle()
    gif_deliver()
    gif_voice()
    gif_tidy()
    write_captions_md()
    print("Done.")


if __name__ == "__main__":
    main()
