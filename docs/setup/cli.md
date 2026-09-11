# Pure command-line setup

Minimal path using only `git`, `python3`, and `pip` — no IDE required.

```bash
git clone https://github.com/btstevens1984az/NestWeaver.git
cd NestWeaver
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev,sim]"

nestweaver doctor
nestweaver sim-demo --scenario all
nestweaver safety-status
nestweaver chat --offline "Find the bottle"
pytest -q
python scripts/generate_demo_gifs.py
```

Useful scripts:

| Script | Purpose |
|--------|---------|
| `scripts/install_sdk.sh` | Create venv + editable install |
| `scripts/run_sim.sh` | Run offline sim demo |
| `scripts/generate_demo_gifs.py` | Regenerate README GIFs |
| `scripts/calibrate_soft_limits.py` | Interactive soft-limit helper |

Environment variables:

| Variable | Default | Meaning |
|----------|---------|---------|
| `NESTWEAVER_OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama base URL |
