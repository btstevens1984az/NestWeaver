#!/usr/bin/env python3
"""Perception node — depth frames + optional Hailo detections."""

from __future__ import annotations

try:
    import rclpy
    from rclpy.node import Node
except ImportError:  # pragma: no cover
    rclpy = None
    Node = object  # type: ignore


class PerceptionNode(Node):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__("nestweaver_perception")
        self.declare_parameter("use_hailo", True)
        self.create_timer(0.1, self._tick)
        self.get_logger().info("NestWeaver perception ready (sim/stub)")

    def _tick(self) -> None:
        # Extension point: RealSense capture → Hailo infer → Detection2DArray
        pass


def main() -> None:
    if rclpy is None:
        raise SystemExit("rclpy not installed — source a ROS 2 workspace first")
    rclpy.init()
    node = PerceptionNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
