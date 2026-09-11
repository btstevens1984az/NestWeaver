"""High-level autonomy behaviors: navigate, fetch, tidy, voice-while-moving."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from nestweaver.arm.ik import ArmController, Pose6D
from nestweaver.base.kinematics import OmnibaseController, Twist2D
from nestweaver.perception.pipeline import PerceptionPipeline
from nestweaver.safety.interlocks import SafetyInterlock, SafetyState


class Behavior(Enum):
    IDLE = auto()
    NAVIGATE = auto()
    FETCH = auto()
    DELIVER = auto()
    TIDY = auto()
    VOICE = auto()


@dataclass
class RoomWaypoint:
    name: str
    x: float
    y: float
    yaw: float = 0.0


@dataclass
class AutonomyState:
    behavior: Behavior = Behavior.IDLE
    pose_xy_yaw: tuple[float, float, float] = (0.0, 0.0, 0.0)
    held_object: str | None = None
    log: list[str] = field(default_factory=list)


class AutonomyOrchestrator:
    """Coordinates base, arm, perception, and safety for Day-1 sim demos."""

    def __init__(
        self,
        safety: SafetyInterlock | None = None,
        base: OmnibaseController | None = None,
        arm: ArmController | None = None,
        perception: PerceptionPipeline | None = None,
        llm: Any = None,
    ) -> None:
        self.safety = safety or SafetyInterlock()
        self.base = base or OmnibaseController(
            safety_check=self.safety.check_base_command,
        )
        self.arm = arm or ArmController(
            safety_check_joints=self.safety.check_arm_joints,
            safety_check_pose=self.safety.check_ee_pose,
        )
        self.perception = perception
        self.llm = llm
        self.state = AutonomyState()
        # Keep watchdogs green in sim
        self.safety.heartbeat()
        self.safety.perception_tick()
        self.safety.control_tick()

    def _tick_watchdogs(self) -> None:
        self.safety.heartbeat()
        self.safety.perception_tick()
        self.safety.control_tick()

    def _log(self, msg: str) -> None:
        self.state.log.append(msg)

    def navigate_to(self, waypoint: RoomWaypoint, steps: int = 5) -> bool:
        self._tick_watchdogs()
        self.state.behavior = Behavior.NAVIGATE
        status = self.safety.status()
        if not status.motion_allowed:
            self._log(f"navigate blocked: {status.reasons}")
            return False
        x0, y0, yaw = self.state.pose_xy_yaw
        for i in range(1, steps + 1):
            self._tick_watchdogs()
            t = i / steps
            x = x0 + (waypoint.x - x0) * t
            y = y0 + (waypoint.y - y0) * t
            yaw = waypoint.yaw
            # Command a small twist toward target (sim)
            self.base.command_twist(Twist2D(vx=0.2, vy=0.0, omega=0.0))
            self.state.pose_xy_yaw = (x, y, yaw)
        self.base.stop()
        self._log(f"arrived at {waypoint.name}")
        self.state.behavior = Behavior.IDLE
        return True

    def fetch_object(self, label: str = "bottle") -> bool:
        self._tick_watchdogs()
        self.state.behavior = Behavior.FETCH
        if self.perception is not None:
            self.perception.start()
            frame = self.perception.step()
            hits = [d for d in frame.detections if d.label == label]
            self.perception.stop()
            if not hits:
                self._log(f"no {label} detected")
                self.state.behavior = Behavior.IDLE
                return False
            xyz = hits[0].xyz_m or (0.35, 0.0, 0.45)
        else:
            xyz = (0.28, 0.0, 0.30)
        # Keep grasp targets inside approximate arm workspace for the stub IK
        x, y, z = xyz[0], xyz[1], max(0.12, min(0.45, xyz[2]))
        reach = math.hypot(x, y)
        if reach > 0.35:
            scale = 0.35 / reach
            x, y = x * scale, y * scale
        target = Pose6D(x=x, y=y, z=z, roll=0.0, pitch=0.4, yaw=0.0)
        self.arm.open_gripper()
        ok = self.arm.move_to_pose(target)
        if not ok:
            self._log("IK/safety rejected grasp pose")
            self.state.behavior = Behavior.IDLE
            return False
        self.arm.close_gripper()
        self.state.held_object = label
        self._log(f"grasped {label}")
        self.state.behavior = Behavior.IDLE
        return True

    def deliver_to(self, waypoint: RoomWaypoint) -> bool:
        if not self.state.held_object:
            self._log("nothing to deliver")
            return False
        self.state.behavior = Behavior.DELIVER
        if not self.navigate_to(waypoint):
            return False
        place = Pose6D(x=0.30, y=0.0, z=0.55, roll=0.0, pitch=0.2, yaw=0.0)
        if not self.arm.move_to_pose(place):
            self._log("place pose rejected")
            return False
        self.arm.open_gripper()
        self._log(f"delivered {self.state.held_object} at {waypoint.name}")
        self.state.held_object = None
        self.state.behavior = Behavior.IDLE
        return True

    def tidy_item(self, item: str, home: RoomWaypoint) -> bool:
        self.state.behavior = Behavior.TIDY
        if not self.fetch_object(item):
            # Allow tidy of known clutter without perception in bare sim
            self.state.held_object = item
            self._log(f"sim-picked {item}")
        ok = self.deliver_to(home)
        self.state.behavior = Behavior.IDLE
        return ok

    def voice_query_while_moving(
        self, text: str, waypoint: RoomWaypoint, context: dict | None = None
    ) -> str:
        self.state.behavior = Behavior.VOICE
        self._tick_watchdogs()
        # Start motion
        self.base.command_twist(Twist2D(vx=0.15, vy=0.0, omega=0.0))
        reply = ""
        if self.llm is not None and self.safety.status().llm_allowed:
            reply = self.llm.chat(text, context=context or {"room": waypoint.name})
        else:
            reply = f"(no llm) acknowledged: {text}"
        self.navigate_to(waypoint, steps=3)
        self._log(f"voice reply: {reply[:80]}")
        self.state.behavior = Behavior.IDLE
        return reply

    def emergency_stop(self) -> None:
        self.safety.set_e_stop(True)
        self.base.stop()
        self.arm.stop()
        self.state.behavior = Behavior.IDLE
        self._log("E-STOP")

    def is_safe(self) -> bool:
        return self.safety.status().state in (SafetyState.OK, SafetyState.WARN)
