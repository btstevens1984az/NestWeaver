from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    """Day-1 software bringup (nodes run as stubs without hardware)."""
    return LaunchDescription(
        [
            Node(
                package="nestweaver_base_driver",
                executable="base_driver_node",
                name="base_driver",
                output="screen",
            ),
            Node(
                package="nestweaver_arm_control",
                executable="arm_control_node",
                name="arm_control",
                output="screen",
            ),
            Node(
                package="nestweaver_perception",
                executable="perception_node",
                name="perception",
                output="screen",
                parameters=[{"use_hailo": True}],
            ),
            Node(
                package="nestweaver_navigation",
                executable="navigation_node",
                name="navigation",
                output="screen",
            ),
            Node(
                package="nestweaver_tidy_behaviors",
                executable="tidy_behaviors_node",
                name="tidy_behaviors",
                output="screen",
            ),
            Node(
                package="nestweaver_voice_llm",
                executable="voice_llm_node",
                name="voice_llm",
                output="screen",
                parameters=[
                    {"ollama_url": "http://127.0.0.1:11434", "model": "llama3.2:3b"}
                ],
            ),
        ]
    )
