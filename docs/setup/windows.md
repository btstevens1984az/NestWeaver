# Windows setup

## Options

1. **WSL2 (recommended)** — Ubuntu 22.04/24.04 for ROS 2 + Python SDK  
2. **Native Python** — SDK + sim demos only (no ROS 2 on native Windows)  
3. **Docker Desktop** — see [docker.md](docker.md)

## Native Python (SDK / sim)

1. Install [Python 3.11+](https://www.python.org/downloads/) (check “Add to PATH”).  
2. Open **PowerShell** or **Windows Terminal**:

```powershell
git clone https://github.com/btstevens1984az/NestWeaver.git
cd NestWeaver
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,sim]"
nestweaver doctor
nestweaver sim-demo
pytest -q
```

## WSL2 + ROS 2

```powershell
wsl --install -d Ubuntu-24.04
```

Inside WSL, follow [linux.md](linux.md) for ROS 2 Jazzy/Humble and the Python SDK.

## Ollama on Windows

Install from [https://ollama.com](https://ollama.com), then:

```powershell
ollama pull llama3.2:3b
nestweaver chat "How do I tidy a living room safely?"
```
