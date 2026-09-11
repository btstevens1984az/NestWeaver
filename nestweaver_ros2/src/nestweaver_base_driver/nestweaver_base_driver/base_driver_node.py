#!/usr/bin/env python3
"""Base driver ROS 2 node — publishes odom twist, subscribes to cmd_vel."""

from __future__ import annotations

try:
    import rclpy
    from geometry_msgs.msg import Twist
    from rclpy.node import Node
except ImportError:  # pragma: no cover - allows docs/CI without ROS
    rclpy = None
    Node = object  # type: ignore
    Twist = object  # type: ignore


class BaseDriverNode(Node):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__("nestweaver_base_driver")
        self.declare_parameter("max_linear_speed_mps", 0.55)
        self._cmd = Twist()
        self.create_subscription(Twist, "cmd_vel", self._on_cmd, 10)
        self.create_timer(0.05, self._tick)
        self.get_logger().info("NestWeaver base driver ready (sim/stub)")

    def _on_cmd(self, msg: Twist) -> None:
        max_v = float(self.get_parameter("max_linear_speed_mps").value)
        msg.linear.x = max(-max_v, min(max_v, msg.linear.x))
        msg.linear.y = max(-max_v, min(max_v, msg.linear.y))
        self._cmd = msg

    def _tick(self) -> None:
        # Extension point: convert Twist → mecanum wheel speeds → motor driver
        _ = self._cmd


def main() -> None:
    if rclpy is None:
        raise SystemExit("rclpy not installed — source a ROS 2 workspace first")
    rclpy.init()
    node = BaseDriverNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
