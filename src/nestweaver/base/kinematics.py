"""Omnidirectional (mecanum) base kinematics — stubs with clear hardware extension points."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Twist2D:
    vx: float  # m/s forward
    vy: float  # m/s left
    omega: float  # rad/s CCW


@dataclass
class WheelSpeeds:
    """Four mecanum wheels: FL, FR, RL, RR (rad/s)."""

    fl: float
    fr: float
    rl: float
    rr: float


@dataclass
class MecanumGeometry:
    wheel_radius_m: float = 0.05
    track_width_m: float = 0.30  # left-right distance between wheel centers
    wheelbase_m: float = 0.28  # front-rear distance between wheel centers


class BaseDriver(ABC):
    """Hardware extension point for motor drivers / ESCs."""

    @abstractmethod
    def apply_wheel_speeds(self, speeds: WheelSpeeds) -> None: ...

    @abstractmethod
    def read_odometry_twist(self) -> Twist2D: ...

    @abstractmethod
    def stop(self) -> None: ...


class SimulatedBaseDriver(BaseDriver):
    """In-process sim for Day-1 demos without hardware."""

    def __init__(self) -> None:
        self._speeds = WheelSpeeds(0.0, 0.0, 0.0, 0.0)
        self._twist = Twist2D(0.0, 0.0, 0.0)

    def apply_wheel_speeds(self, speeds: WheelSpeeds) -> None:
        self._speeds = speeds

    def read_odometry_twist(self) -> Twist2D:
        return self._twist

    def stop(self) -> None:
        self._speeds = WheelSpeeds(0.0, 0.0, 0.0, 0.0)
        self._twist = Twist2D(0.0, 0.0, 0.0)

    def set_simulated_twist(self, twist: Twist2D) -> None:
        self._twist = twist


class MecanumKinematics:
    """Forward/inverse kinematics for a rectangular mecanum base."""

    def __init__(self, geometry: MecanumGeometry | None = None) -> None:
        self.geometry = geometry or MecanumGeometry()

    def inverse(self, twist: Twist2D) -> WheelSpeeds:
        r = self.geometry.wheel_radius_m
        lx = self.geometry.wheelbase_m / 2.0
        ly = self.geometry.track_width_m / 2.0
        vx, vy, w = twist.vx, twist.vy, twist.omega
        # Standard mecanum inverse IK
        fl = (1 / r) * (vx - vy - (lx + ly) * w)
        fr = (1 / r) * (vx + vy + (lx + ly) * w)
        rl = (1 / r) * (vx + vy - (lx + ly) * w)
        rr = (1 / r) * (vx - vy + (lx + ly) * w)
        return WheelSpeeds(fl=fl, fr=fr, rl=rl, rr=rr)

    def forward(self, speeds: WheelSpeeds) -> Twist2D:
        r = self.geometry.wheel_radius_m
        lx = self.geometry.wheelbase_m / 2.0
        ly = self.geometry.track_width_m / 2.0
        fl, fr, rl, rr = speeds.fl, speeds.fr, speeds.rl, speeds.rr
        vx = (r / 4.0) * (fl + fr + rl + rr)
        vy = (r / 4.0) * (-fl + fr + rl - rr)
        omega = (r / (4.0 * (lx + ly))) * (-fl + fr - rl + rr)
        return Twist2D(vx=vx, vy=vy, omega=omega)


class OmnibaseController:
    """High-level base controller that respects a safety gate callback."""

    def __init__(
        self,
        kinematics: MecanumKinematics | None = None,
        driver: BaseDriver | None = None,
        safety_check=None,
    ) -> None:
        self.kinematics = kinematics or MecanumKinematics()
        self.driver = driver or SimulatedBaseDriver()
        self.safety_check = safety_check

    def command_twist(self, twist: Twist2D) -> WheelSpeeds:
        if self.safety_check is not None:
            status = self.safety_check(twist.vx, twist.vy, twist.omega)
            if hasattr(status, "motion_allowed") and not status.motion_allowed:
                self.driver.stop()
                return WheelSpeeds(0.0, 0.0, 0.0, 0.0)
        speeds = self.kinematics.inverse(twist)
        self.driver.apply_wheel_speeds(speeds)
        if isinstance(self.driver, SimulatedBaseDriver):
            self.driver.set_simulated_twist(twist)
        return speeds

    def stop(self) -> None:
        self.driver.stop()

    def rotate_in_place(self, omega: float) -> WheelSpeeds:
        return self.command_twist(Twist2D(0.0, 0.0, omega))

    def translate(self, vx: float, vy: float) -> WheelSpeeds:
        return self.command_twist(Twist2D(vx, vy, 0.0))

    @staticmethod
    def heading_error(current_yaw: float, target_yaw: float) -> float:
        err = (target_yaw - current_yaw + math.pi) % (2 * math.pi) - math.pi
        return err
