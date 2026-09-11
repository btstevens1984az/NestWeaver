#!/usr/bin/env python3
"""Tidy / fetch behavior node."""

from __future__ import annotations

try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String
except ImportError:  # pragma: no cover
    rclpy = None
    Node = object  # type: ignore
    String = object  # type: ignore


class TidyBehaviorsNode(Node):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__("nestweaver_tidy_behaviors")
        self.create_subscription(String, "behavior/command", self._on_cmd, 10)
        self.get_logger().info("NestWeaver tidy behaviors ready")

    def _on_cmd(self, msg: String) -> None:
        self.get_logger().info(f"behavior command: {msg.data}")
        # Extension point: map to AutonomyOrchestrator actions / BT.CPP trees


def main() -> None:
    if rclpy is None:
        raise SystemExit("rclpy not installed — source a ROS 2 workspace first")
    rclpy.init()
    node = TidyBehaviorsNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
