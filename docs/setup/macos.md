# macOS setup

## Python SDK (Apple Silicon or Intel)

```bash
git clone https://github.com/btstevens1984az/NestWeaver.git
cd NestWeaver
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev,sim]"
nestweaver doctor
nestweaver sim-demo --scenario all
pytest -q
```

## Ollama

```bash
brew install ollama
ollama serve   # if not already running as a service
ollama pull llama3.2:3b
nestweaver chat "Plan a fetch for a water bottle"
```

## ROS 2 on macOS

Official ROS 2 desktop packages target Linux. On macOS use one of:

- **Docker** — [docker.md](docker.md)  
- **Linux VM / remote Pi** — build `nestweaver_ros2` on the robot SBC  
- **colcon from source** — advanced; not required for Day-1 SDK work  

## Demo GIFs

```bash
python scripts/generate_demo_gifs.py
open docs/media/demo-navigate.gif
```
