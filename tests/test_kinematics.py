"""Tests for mecanum kinematics and arm IK stubs."""

from __future__ import annotations

from nestweaver.arm import ApproximateIKSolver, ArmController, Pose6D
from nestweaver.base import MecanumKinematics, OmnibaseController, Twist2D
from nestweaver.safety import SafetyInterlock


def test_mecanum_roundtrip() -> None:
    kin = MecanumKinematics()
    twist = Twist2D(0.2, -0.1, 0.3)
    wheels = kin.inverse(twist)
    back = kin.forward(wheels)
    assert abs(back.vx - twist.vx) < 1e-6
    assert abs(back.vy - twist.vy) < 1e-6
    assert abs(back.omega - twist.omega) < 1e-6


def test_base_respects_safety() -> None:
    safety = SafetyInterlock()
    safety.heartbeat()
    safety.perception_tick()
    safety.control_tick()
    ctrl = OmnibaseController(safety_check=safety.check_base_command)
    speeds = ctrl.command_twist(Twist2D(0.1, 0.0, 0.0))
    assert speeds.fl != 0.0
    safety.set_e_stop(True)
    speeds = ctrl.command_twist(Twist2D(0.1, 0.0, 0.0))
    assert speeds.fl == 0.0


def test_ik_reachable() -> None:
    solver = ApproximateIKSolver()
    target = Pose6D(0.25, 0.05, 0.35, 0.0, 0.3, 0.0)
    q = solver.solve(target)
    assert q is not None
    fk = solver.forward(q)
    assert fk.z > 0.0


def test_arm_controller_with_safety() -> None:
    safety = SafetyInterlock()
    safety.heartbeat()
    safety.perception_tick()
    safety.control_tick()
    arm = ArmController(
        safety_check_joints=safety.check_arm_joints,
        safety_check_pose=safety.check_ee_pose,
    )
    assert arm.move_to_pose(Pose6D(0.3, 0.0, 0.4, 0.0, 0.2, 0.0))
