# PowerShell setup

Works on **Windows PowerShell 5.1+** and **PowerShell 7+** (Windows, macOS, Linux).

```powershell
git clone https://github.com/btstevens1984az/NestWeaver.git
Set-Location NestWeaver
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
# On macOS/Linux pwsh:
# python3 -m venv .venv; . ./.venv/bin/Activate.ps1

python -m pip install --upgrade pip
pip install -e ".[dev,sim]"

nestweaver doctor
nestweaver sim-demo --scenario tidy
pytest -q
python scripts/generate_demo_gifs.py
```

If execution policy blocks activation on Windows:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Docker from PowerShell:

```powershell
docker compose up --build
```

Optional: use `scripts/install_sdk.ps1` for a one-shot install.
