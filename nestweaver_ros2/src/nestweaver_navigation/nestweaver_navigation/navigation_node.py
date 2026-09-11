#!/usr/bin/env python3
"""Navigation helper — waypoint follower bridge to Nav2."""

from __future__ import annotations

try:
    import rclpy
    from rclpy.node import Node
except ImportError:  # pragma: no cover
    rclpy = None
    Node = object  # type: ignore


class NavigationNode(Node):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__("nestweaver_navigation")
        self.declare_parameter("room_config", "configs/rooms/apartment_demo.yaml")
        self.get_logger().info("NestWeaver navigation helper ready — wire to Nav2 NavigateToPose")


def main() -> None:
    if rclpy is None:
        raise SystemExit("rclpy not installed — source a ROS 2 workspace first")
    rclpy.init()
    node = NavigationNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
