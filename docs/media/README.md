# Demo media — AI short videos

All demos are **generative image-to-video** (~5s product clips), not optical-flow
warps of stills and not crossfade slideshows.

## Pipeline

`scripts/generate_demo_videos.py` is the source of truth:

| Backend | What it does |
|---------|----------------|
| `svd-hf` | Stable Video Diffusion via Hugging Face Space |
| `wan-hf` | Wan 2.2 I2V via Hugging Face Space |
| `svd-local` | Local SVD (`stabilityai/stable-video-diffusion-img2vid`) on CPU |
| `encode` | Re-encode existing generative MP4s → README MP4 + GIF |

Optical-flow / parallax still-warps are **hard-disabled** (do not ship).

```bash
.venv/bin/python scripts/generate_demo_videos.py --backend auto
.venv/bin/python scripts/generate_demo_videos.py --backend encode
```

Legacy `scripts/generate_demo_gifs.py` may still exist for historical OF experiments;
prefer `generate_demo_videos.py`.

## Files

| Stem | Scene | Typical generator |
|------|--------|-------------------|
| `demo-navigate` | Driving through living room | SVD (HF Space) |
| `demo-pick-bottle` | Pick water bottle | SVD (HF Space) |
| `demo-deliver` | Deliver / handoff | Wan 2.2 I2V (HF Space) |
| `demo-voice-llm` | Voice / LED while rolling | Wan 2.2 I2V (HF Space) |
| `demo-tidy` | Tidy clutter into basket | SVD / Wan (see `_i2v_meta/`) |

Committed outputs per stem: `docs/media/<stem>.mp4` + `docs/media/<stem>.gif`  
Raw generative sources: `docs/media/video_raw/<scene>.mp4`  
Seeds: `frames/{navigate,pick,deliver,voice,tidy}/`  
Per-clip provenance: `_i2v_meta/<scene>.json`
