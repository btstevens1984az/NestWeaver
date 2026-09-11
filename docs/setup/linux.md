# Linux setup

Tested targets: Ubuntu 22.04 (Humble) and 24.04 (Jazzy).

## Python SDK

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip git
git clone https://github.com/btstevens1984az/NestWeaver.git
cd NestWeaver
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev,sim]"
nestweaver doctor
nestweaver sim-demo
pytest -q
```

## Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b
nestweaver chat "What safety checks should I run before enabling motors?"
```

## ROS 2 workspace

```bash
# After installing ROS 2 Humble or Jazzy per docs.ros.org
source /opt/ros/$ROS_DISTRO/setup.bash
cd nestweaver_ros2
sudo rosdep init 2>/dev/null || true
rosdep update
rosdep install --from-paths src -y --ignore-src
colcon build --symlink-install
source install/setup.bash
ros2 launch nestweaver_bringup nestweaver.launch.py
```

## On-robot (Raspberry Pi OS / Ubuntu for Pi)

1. Flash 64-bit OS, enable SSH.  
2. Install HailoRT per Hailo docs matching your HAT/module.  
3. Install NestWeaver SDK + ROS 2 (if using Nav2 on-device).  
4. Copy `configs/robots/nestweaver_alpha.yaml` and calibrate soft limits.
