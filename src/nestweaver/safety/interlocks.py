"""Safety interlocks for NestWeaver: e-stop, soft limits, collision, battery, watchdogs."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto


class SafetyState(Enum):
    OK = auto()
    WARN = auto()
    FAULT = auto()
    E_STOP = auto()


@dataclass
class SoftLimits:
    """Cartesian and joint soft limits (meters / radians)."""

    x_min: float = -2.0
    x_max: float = 2.0
    y_min: float = -2.0
    y_max: float = 2.0
    z_min: float = 0.05
    z_max: float = 1.2
    joint_min: tuple[float, ...] = (-2.8, -1.8, -2.5, -2.8, -1.8, -2.8)
    joint_max: tuple[float, ...] = (2.8, 1.8, 2.5, 2.8, 1.8, 2.8)
    max_linear_speed_mps: float = 0.6
    max_angular_speed_rps: float = 1.2
    max_joint_speed_rps: float = 1.5


@dataclass
class BatteryPolicy:
    warn_fraction: float = 0.25
    cutoff_fraction: float = 0.12
    critical_fraction: float = 0.08


@dataclass
class WatchdogConfig:
    heartbeat_timeout_s: float = 0.5
    perception_timeout_s: float = 1.0
    control_timeout_s: float = 0.25


@dataclass
class SafetyStatus:
    state: SafetyState = SafetyState.OK
    reasons: list[str] = field(default_factory=list)
    motion_allowed: bool = True
    arm_allowed: bool = True
    llm_allowed: bool = True


class SafetyInterlock:
    """Central safety arbitrator — all motion commands must pass through here.

    Hardware drivers should call :meth:`assert_motion_allowed` before applying
    wheel or joint commands. Faults latch until :meth:`clear_faults` after the
    underlying condition is resolved and the operator acknowledges.
    """

    def __init__(
        self,
        soft_limits: SoftLimits | None = None,
        battery: BatteryPolicy | None = None,
        watchdog: WatchdogConfig | None = None,
        on_state_change: Callable[[SafetyStatus], None] | None = None,
    ) -> None:
        self.soft_limits = soft_limits or SoftLimits()
        self.battery = battery or BatteryPolicy()
        self.watchdog = watchdog or WatchdogConfig()
        self._on_state_change = on_state_change
        self._lock = threading.RLock()
        self._e_stop = False
        self._collision = False
        self._geofence_breach = False
        self._child_pet_near = False
        self._battery_fraction = 1.0
        self._latched_faults: list[str] = []
        self._last_heartbeat = time.monotonic()
        self._last_perception = time.monotonic()
        self._last_control = time.monotonic()
        self._torque_limit_nm = 8.0
        self._status = SafetyStatus()

    # --- hardware / sensor inputs -------------------------------------------------

    def set_e_stop(self, pressed: bool) -> SafetyStatus:
        with self._lock:
            self._e_stop = pressed
            if pressed:
                self._latched_faults.append("e_stop_pressed")
            return self._reevaluate()

    def set_collision(self, detected: bool, reason: str = "collision") -> SafetyStatus:
        with self._lock:
            self._collision = detected
            if detected:
                self._latched_faults.append(reason)
            return self._reevaluate()

    def set_geofence_breach(self, breached: bool) -> SafetyStatus:
        with self._lock:
            self._geofence_breach = breached
            if breached:
                self._latched_faults.append("geofence_breach")
            return self._reevaluate()

    def set_child_pet_proximity(self, near: bool) -> SafetyStatus:
        with self._lock:
            self._child_pet_near = near
            return self._reevaluate()

    def set_battery_fraction(self, fraction: float) -> SafetyStatus:
        with self._lock:
            self._battery_fraction = max(0.0, min(1.0, fraction))
            if self._battery_fraction <= self.battery.cutoff_fraction:
                self._latched_faults.append("battery_cutoff")
            return self._reevaluate()

    def heartbeat(self) -> None:
        with self._lock:
            self._last_heartbeat = time.monotonic()

    def perception_tick(self) -> None:
        with self._lock:
            self._last_perception = time.monotonic()

    def control_tick(self) -> None:
        with self._lock:
            self._last_control = time.monotonic()

    def set_torque_limit_nm(self, limit_nm: float) -> None:
        with self._lock:
            self._torque_limit_nm = max(0.5, limit_nm)

    # --- command gates ------------------------------------------------------------

    def check_base_command(self, vx: float, vy: float, omega: float) -> SafetyStatus:
        with self._lock:
            status = self._reevaluate()
            if not status.motion_allowed:
                return status
            lim = self.soft_limits
            speed = (vx * vx + vy * vy) ** 0.5
            if speed > lim.max_linear_speed_mps + 1e-6:
                return self._reject("linear_speed_limit")
            if abs(omega) > lim.max_angular_speed_rps + 1e-6:
                return self._reject("angular_speed_limit")
            return status

    def check_arm_joints(self, joints: list[float] | tuple[float, ...]) -> SafetyStatus:
        with self._lock:
            status = self._reevaluate()
            if not status.arm_allowed:
                return status
            jmin, jmax = self.soft_limits.joint_min, self.soft_limits.joint_max
            if len(joints) != len(jmin):
                return self._reject("joint_count_mismatch")
            for i, q in enumerate(joints):
                if q < jmin[i] - 1e-6 or q > jmax[i] + 1e-6:
                    return self._reject(f"joint_{i}_soft_limit")
            return status

    def check_ee_pose(self, x: float, y: float, z: float) -> SafetyStatus:
        with self._lock:
            status = self._reevaluate()
            if not status.arm_allowed:
                return status
            lim = self.soft_limits
            if not (lim.x_min <= x <= lim.x_max):
                return self._reject("ee_x_soft_limit")
            if not (lim.y_min <= y <= lim.y_max):
                return self._reject("ee_y_soft_limit")
            if not (lim.z_min <= z <= lim.z_max):
                return self._reject("ee_z_soft_limit")
            return status

    def check_torque(self, torque_nm: float) -> SafetyStatus:
        with self._lock:
            status = self._reevaluate()
            if abs(torque_nm) > self._torque_limit_nm + 1e-6:
                self._latched_faults.append("torque_limit")
                return self._reevaluate()
            return status

    def assert_motion_allowed(self) -> None:
        status = self.status()
        if not status.motion_allowed:
            raise RuntimeError(f"Motion blocked: {', '.join(status.reasons) or status.state.name}")

    def clear_faults(self, acknowledge: bool = False) -> SafetyStatus:
        """Clear latched faults only when e-stop released and operator acknowledges."""
        with self._lock:
            if self._e_stop:
                return self._reevaluate()
            if not acknowledge:
                return self._reject("ack_required")
            self._latched_faults.clear()
            self._collision = False
            self._geofence_breach = False
            return self._reevaluate()

    def status(self) -> SafetyStatus:
        with self._lock:
            return self._reevaluate()

    # --- internals ----------------------------------------------------------------

    def _reject(self, reason: str) -> SafetyStatus:
        self._latched_faults.append(reason)
        return self._reevaluate()

    def _reevaluate(self) -> SafetyStatus:
        reasons: list[str] = []
        state = SafetyState.OK
        now = time.monotonic()

        if self._e_stop or "e_stop_pressed" in self._latched_faults:
            reasons.append("e_stop")
            state = SafetyState.E_STOP

        if self._collision or any(r.startswith("collision") for r in self._latched_faults):
            reasons.append("collision")
            state = SafetyState.FAULT if state != SafetyState.E_STOP else state

        if self._geofence_breach or "geofence_breach" in self._latched_faults:
            reasons.append("geofence")
            state = SafetyState.FAULT if state == SafetyState.OK else state

        if self._battery_fraction <= self.battery.critical_fraction:
            reasons.append("battery_critical")
            state = SafetyState.FAULT if state == SafetyState.OK else state
        elif self._battery_fraction <= self.battery.cutoff_fraction:
            reasons.append("battery_cutoff")
            state = SafetyState.FAULT if state == SafetyState.OK else state
        elif self._battery_fraction <= self.battery.warn_fraction:
            reasons.append("battery_low")
            if state == SafetyState.OK:
                state = SafetyState.WARN

        if now - self._last_heartbeat > self.watchdog.heartbeat_timeout_s:
            reasons.append("heartbeat_watchdog")
            state = SafetyState.FAULT if state != SafetyState.E_STOP else state
        if now - self._last_perception > self.watchdog.perception_timeout_s:
            reasons.append("perception_watchdog")
            if state == SafetyState.OK:
                state = SafetyState.WARN
        if now - self._last_control > self.watchdog.control_timeout_s:
            reasons.append("control_watchdog")
            state = SafetyState.FAULT if state != SafetyState.E_STOP else state

        # Deduplicate other latched reasons
        for r in self._latched_faults:
            if r not in reasons and r not in ("e_stop_pressed",):
                reasons.append(r)
                if state == SafetyState.OK:
                    state = SafetyState.FAULT

        child_pet_slow = self._child_pet_near and state == SafetyState.OK
        if self._child_pet_near:
            reasons.append("child_pet_proximity")
            if state == SafetyState.OK:
                state = SafetyState.WARN

        motion_allowed = state in (SafetyState.OK, SafetyState.WARN) and not self._e_stop
        if state in (SafetyState.FAULT, SafetyState.E_STOP):
            motion_allowed = False
        if "battery_cutoff" in reasons or "battery_critical" in reasons:
            motion_allowed = False

        # Near children/pets: allow motion but planners should reduce speed (flag via WARN)
        arm_allowed = motion_allowed and not child_pet_slow
        llm_allowed = state != SafetyState.E_STOP

        status = SafetyStatus(
            state=state,
            reasons=sorted(set(reasons)),
            motion_allowed=motion_allowed,
            arm_allowed=arm_allowed,
            llm_allowed=llm_allowed,
        )
        prev = self._status
        self._status = status
        if self._on_state_change and (
            prev.state != status.state or prev.reasons != status.reasons
        ):
            self._on_state_change(status)
        return status
