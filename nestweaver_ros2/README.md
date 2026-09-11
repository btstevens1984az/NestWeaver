# NestWeaver ROS 2 workspace

Target distros: **ROS 2 Humble** (Ubuntu 22.04) or **Jazzy** (Ubuntu 24.04).

## Build

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
cd nestweaver_ros2
rosdep install --from-paths src -y --ignore-src
colcon build --symlink-install
source install/setup.bash
ros2 launch nestweaver_bringup nestweaver.launch.py
```

Packages: `nestweaver_bringup`, `nestweaver_base_driver`, `nestweaver_arm_control`,
`nestweaver_perception`, `nestweaver_navigation`, `nestweaver_tidy_behaviors`,
`nestweaver_voice_llm`.

The Python SDK under `src/nestweaver` can run **without** ROS for sim/dev.
