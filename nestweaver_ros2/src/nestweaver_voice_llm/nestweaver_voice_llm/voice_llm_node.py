#!/usr/bin/env python3
"""Voice + local Ollama bridge node."""

from __future__ import annotations

try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String
except ImportError:  # pragma: no cover
    rclpy = None
    Node = object  # type: ignore
    String = object  # type: ignore


class VoiceLLMNode(Node):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__("nestweaver_voice_llm")
        self.declare_parameter("ollama_url", "http://127.0.0.1:11434")
        self.declare_parameter("model", "llama3.2:3b")
        self._pub = self.create_publisher(String, "voice/reply", 10)
        self.create_subscription(String, "voice/utterance", self._on_utterance, 10)
        self.get_logger().info("NestWeaver voice/LLM bridge ready (local Ollama)")

    def _on_utterance(self, msg: String) -> None:
        # Extension point: OllamaClient.chat → TTS → voice/reply
        out = String()
        out.data = f"(stub) heard: {msg.data}"
        self._pub.publish(out)


def main() -> None:
    if rclpy is None:
        raise SystemExit("rclpy not installed — source a ROS 2 workspace first")
    rclpy.init()
    node = VoiceLLMNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
