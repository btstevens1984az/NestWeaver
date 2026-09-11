# Demo media captions

All GIFs are **AI-generated photorealistic product visualizations** — not live
robot camera footage of a shipped unit. They are produced for continuous ~5s
motion (not still-photo slideshows / crossfades).

## Motion pipeline

`scripts/generate_demo_gifs.py` supports:

| Method | What it does |
|--------|----------------|
| `svd-hf` / existing I2V MP4 | Stable Video Diffusion image-to-video, then ffmpeg `minterpolate` → GIF |
| `flow` (default fallback) | Continuous parallax optical-flow warping of a photoreal seed (locomotion + arm-reach flow) |
| `of` | Farneback warp between progressive keyframes (not alpha crossfade) |

Regenerate:

```bash
# Prefer existing I2V MP4s under video_raw/, else HF SVD, else flow synth
.venv/bin/python scripts/generate_demo_gifs.py --method auto

# Force continuous parallax-flow synthesis
.venv/bin/python scripts/generate_demo_gifs.py --method flow
```

## Files

| File | Scene | Typical motion source |
|------|--------|------------------------|
| `demo-navigate.gif` | Omnibase navigating a living room | SVD I2V (HF Space) |
| `demo-pick-bottle.gif` | Arm picking a clear water bottle | Continuous flow synth (I2V when quota/API available) |
| `demo-deliver.gif` | Fetch-and-carry delivery | Continuous flow synth |
| `demo-voice-llm.gif` | Voice / LED while rolling | Continuous flow synth |
| `demo-tidy.gif` | Tidying clutter into a basket | Continuous flow synth |

Optional MP4 intermediates: `video_raw/<scene>.mp4`  
Keyframes / seeds: `frames/{navigate,pick,deliver,voice,tidy}/`  
Robot design lock: `frames/_ref/nestweaver-robot-ref.png`
