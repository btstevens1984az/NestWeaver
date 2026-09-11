# Demo media captions

All GIFs are **AI-generated photorealistic product visualizations** assembled
by `scripts/generate_demo_gifs.py` from keyframes in `frames/`. They are **not**
live robot camera footage of a shipped unit.

| File | Scene |
|------|--------|
| `demo-navigate.gif` | Omnibase navigating a living room around furniture |
| `demo-pick-bottle.gif` | 6-DoF arm picking a clear water bottle |
| `demo-deliver.gif` | Fetch-and-carry delivery to a person / table |
| `demo-voice-llm.gif` | Voice query answered by local Ollama while moving |
| `demo-tidy.gif` | Tidying — clutter item returned to a basket / shelf |

Keyframes: `frames/{navigate,pick,deliver,voice,tidy}/*.png`

Regenerate:

```bash
.venv/bin/python scripts/generate_demo_gifs.py
```
