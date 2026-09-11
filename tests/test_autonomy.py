"""Autonomy orchestrator smoke tests (offline)."""

from nestweaver.autonomy import AutonomyOrchestrator, RoomWaypoint
from nestweaver.llm import OfflineEchoLLM
from nestweaver.perception import PerceptionPipeline, SimulatedDepthCamera
from nestweaver.safety import SafetyInterlock


def test_fetch_deliver_flow() -> None:
    safety = SafetyInterlock()
    safety.heartbeat()
    safety.perception_tick()
    safety.control_tick()
    bot = AutonomyOrchestrator(
        safety=safety,
        perception=PerceptionPipeline(SimulatedDepthCamera()),
        llm=OfflineEchoLLM(),
    )
    assert bot.navigate_to(RoomWaypoint("living", 1.0, 0.0))
    assert bot.fetch_object("bottle")
    assert bot.deliver_to(RoomWaypoint("table", 0.5, 0.2))
    assert bot.state.held_object is None


def test_voice_while_moving() -> None:
    safety = SafetyInterlock()
    safety.heartbeat()
    safety.perception_tick()
    safety.control_tick()
    bot = AutonomyOrchestrator(safety=safety, llm=OfflineEchoLLM())
    reply = bot.voice_query_while_moving("hello", RoomWaypoint("hall", 0.4, 0.0))
    assert "hello" in reply.lower() or "offline" in reply.lower()
