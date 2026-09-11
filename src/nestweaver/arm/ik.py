"""6-DoF arm IK interface stubs with clear hardware extension points."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Pose6D:
    x: float
    y: float
    z: float
    roll: float
    pitch: float
    yaw: float


@dataclass
class JointState:
    positions: tuple[float, float, float, float, float, float]
    velocities: tuple[float, float, float, float, float, float] = (0.0,) * 6


@dataclass
class ArmGeometry:
    """Approximate serial DH-like link lengths for a SO-ARM-class manipulator (meters)."""

    link_lengths: tuple[float, ...] = (0.05, 0.22, 0.20, 0.08, 0.08, 0.06)
    name: str = "so_arm_like"


class ArmDriver(ABC):
    @abstractmethod
    def set_joint_positions(self, joints: JointState) -> None: ...

    @abstractmethod
    def get_joint_state(self) -> JointState: ...

    @abstractmethod
    def set_gripper(self, open_fraction: float) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...


class SimulatedArmDriver(ArmDriver):
    def __init__(self) -> None:
        self._joints = JointState(positions=(0.0,) * 6)
        self._gripper = 1.0

    def set_joint_positions(self, joints: JointState) -> None:
        self._joints = joints

    def get_joint_state(self) -> JointState:
        return self._joints

    def set_gripper(self, open_fraction: float) -> None:
        self._gripper = max(0.0, min(1.0, open_fraction))

    def stop(self) -> None:
        self._joints = JointState(
            positions=self._joints.positions,
            velocities=(0.0,) * 6,
        )


class ArmIKSolver(ABC):
    """Extension point — replace with analytic IK or MoveIt2 / Pinocchio backend."""

    @abstractmethod
    def solve(self, target: Pose6D, seed: JointState | None = None) -> JointState | None: ...

    @abstractmethod
    def forward(self, joints: JointState) -> Pose6D: ...


class ApproximateIKSolver(ArmIKSolver):
    """Lightweight geometric approximation for sim/dev — not for production grasping.

    Production builds should swap this for a calibrated IK backend (MoveIt2, custom
    analytic IK for your arm, or a vendor SDK).
    """

    def __init__(self, geometry: ArmGeometry | None = None) -> None:
        self.geometry = geometry or ArmGeometry()

    def solve(self, target: Pose6D, seed: JointState | None = None) -> JointState | None:
        L = self.geometry.link_lengths
        L1, L2 = L[1], L[2]
        base = math.atan2(target.y, target.x)
        r = math.hypot(target.x, target.y)
        z = target.z - L[0]
        dist = math.hypot(r, z)
        max_reach = L1 + L2 - 1e-3
        min_reach = abs(L1 - L2) + 1e-3
        if dist < 1e-6:
            return None
        # Scale into reachable annulus instead of hard-failing near-workspace poses
        if dist > max_reach:
            scale = max_reach / dist
            r *= scale
            z *= scale
            dist = max_reach
        elif dist < min_reach:
            scale = min_reach / dist
            r *= scale
            z *= scale
            dist = min_reach
        cos_e = (L1 * L1 + L2 * L2 - dist * dist) / (2.0 * L1 * L2)
        cos_e = max(-1.0, min(1.0, cos_e))
        elbow = math.pi - math.acos(cos_e)
        alpha = math.atan2(z, r)
        beta = math.acos(max(-1.0, min(1.0, (L1 * L1 + dist * dist - L2 * L2) / (2.0 * L1 * dist))))
        shoulder = alpha + beta
        wrist_pitch = target.pitch
        wrist_roll = target.roll
        wrist_yaw = target.yaw - base
        seed_pos = seed.positions if seed else (0.0,) * 6
        q = (
            0.85 * base + 0.15 * seed_pos[0],
            0.85 * shoulder + 0.15 * seed_pos[1],
            0.85 * elbow + 0.15 * seed_pos[2],
            0.85 * wrist_yaw + 0.15 * seed_pos[3],
            0.85 * wrist_pitch + 0.15 * seed_pos[4],
            0.85 * wrist_roll + 0.15 * seed_pos[5],
        )
        return JointState(positions=q)

    def forward(self, joints: JointState) -> Pose6D:
        L = self.geometry.link_lengths
        q = joints.positions
        x = (L[1] * math.cos(q[1]) + L[2] * math.cos(q[1] + q[2])) * math.cos(q[0])
        y = (L[1] * math.cos(q[1]) + L[2] * math.cos(q[1] + q[2])) * math.sin(q[0])
        z = L[0] + L[1] * math.sin(q[1]) + L[2] * math.sin(q[1] + q[2])
        return Pose6D(x=x, y=y, z=z, roll=q[5], pitch=q[4], yaw=q[0] + q[3])


class ArmController:
    def __init__(
        self,
        solver: ArmIKSolver | None = None,
        driver: ArmDriver | None = None,
        safety_check_joints=None,
        safety_check_pose=None,
    ) -> None:
        self.solver = solver or ApproximateIKSolver()
        self.driver = driver or SimulatedArmDriver()
        self.safety_check_joints = safety_check_joints
        self.safety_check_pose = safety_check_pose

    def move_to_pose(self, target: Pose6D) -> bool:
        if self.safety_check_pose is not None:
            status = self.safety_check_pose(target.x, target.y, target.z)
            if hasattr(status, "arm_allowed") and not status.arm_allowed:
                return False
        seed = self.driver.get_joint_state()
        solution = self.solver.solve(target, seed=seed)
        if solution is None:
            return False
        if self.safety_check_joints is not None:
            status = self.safety_check_joints(list(solution.positions))
            if hasattr(status, "arm_allowed") and not status.arm_allowed:
                return False
        self.driver.set_joint_positions(solution)
        return True

    def open_gripper(self) -> None:
        self.driver.set_gripper(1.0)

    def close_gripper(self) -> None:
        self.driver.set_gripper(0.0)

    def stop(self) -> None:
        self.driver.stop()
