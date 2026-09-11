#!/usr/bin/env python3
"""Arm control ROS 2 node — joint command bridge + IK stub."""

from __future__ import annotations

try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import Float32MultiArray
except ImportError:  # pragma: no cover
    rclpy = None
    Node = object  # type: ignore
    Float32MultiArray = object  # type: ignore


class ArmControlNode(Node):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__("nestweaver_arm_control")
        self.create_subscription(Float32MultiArray, "arm/joint_cmd", self._on_joints, 10)
        self.get_logger().info("NestWeaver arm control ready (sim/stub)")

    def _on_joints(self, msg: Float32MultiArray) -> None:
        if len(msg.data) != 6:
            self.get_logger().warn("expected 6 joint positions")
            return
        # Extension point: safety check → driver.set_joint_positions


def main() -> None:
    if rclpy is None:
        raise SystemExit("rclpy not installed — source a ROS 2 workspace first")
    rclpy.init()
    node = ArmControlNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
