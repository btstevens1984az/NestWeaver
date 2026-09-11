# Contributing to NestWeaver

Thanks for helping build a privacy-first home companion robot.

## Quick path

1. Fork and clone the repo.  
2. `python3 -m venv .venv && source .venv/bin/activate`  
3. `pip install -e ".[dev,sim]"`  
4. `pytest -q` and `ruff check src tests scripts`  
5. Open a PR with a clear description and test notes.

## Guidelines

- Prefer small, focused PRs.  
- Real safety behavior changes need tests in `tests/test_safety.py`.  
- Do not commit secrets, private keys, or proprietary HEF weights you lack rights to redistribute.  
- Demo GIFs must remain clearly labeled as simulated visualizations.  
- Hardware docs should include voltages/currents when known.

## Code style

- Python 3.10+, type hints encouraged.  
- `ruff` for lint.  
- ROS 2 packages follow ament_python layout under `nestweaver_ros2/`.

## Community

Be kind. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
