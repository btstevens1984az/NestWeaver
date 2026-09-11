"""Unit tests for NestWeaver safety interlocks."""

from __future__ import annotations

import pytest

from nestweaver.safety import SafetyInterlock, SafetyState, SoftLimits, WatchdogConfig


@pytest.fixture
def safety() -> SafetyInterlock:
    s = SafetyInterlock(
        watchdog=WatchdogConfig(
            heartbeat_timeout_s=2.0,
            perception_timeout_s=2.0,
            control_timeout_s=2.0,
        )
    )
    s.heartbeat()
    s.perception_tick()
    s.control_tick()
    return s


def test_ok_allows_motion(safety: SafetyInterlock) -> None:
    st = safety.status()
    assert st.state == SafetyState.OK
    assert st.motion_allowed is True
    assert safety.check_base_command(0.2, 0.0, 0.1).motion_allowed


def test_e_stop_blocks_motion(safety: SafetyInterlock) -> None:
    safety.set_e_stop(True)
    st = safety.status()
    assert st.state == SafetyState.E_STOP
    assert st.motion_allowed is False
    with pytest.raises(RuntimeError):
        safety.assert_motion_allowed()


def test_e_stop_requires_ack_to_clear(safety: SafetyInterlock) -> None:
    safety.set_e_stop(True)
    safety.set_e_stop(False)
    st = safety.clear_faults(acknowledge=False)
    assert st.motion_allowed is False
    st = safety.clear_faults(acknowledge=True)
    safety.heartbeat()
    safety.perception_tick()
    safety.control_tick()
    st = safety.status()
    assert st.motion_allowed is True


def test_speed_limit(safety: SafetyInterlock) -> None:
    st = safety.check_base_command(5.0, 0.0, 0.0)
    assert st.motion_allowed is False
    assert st.state == SafetyState.FAULT or any("speed" in r for r in st.reasons)


def test_joint_soft_limits(safety: SafetyInterlock) -> None:
    bad = [0.0, 0.0, 0.0, 0.0, 0.0, 9.0]
    st = safety.check_arm_joints(bad)
    assert st.arm_allowed is False or st.motion_allowed is False


def test_ee_pose_limits(safety: SafetyInterlock) -> None:
    st = safety.check_ee_pose(0.3, 0.0, 0.4)
    assert st.arm_allowed is True
    st = safety.check_ee_pose(0.3, 0.0, 5.0)
    assert st.arm_allowed is False or st.state == SafetyState.FAULT


def test_battery_cutoff(safety: SafetyInterlock) -> None:
    safety.set_battery_fraction(0.05)
    st = safety.status()
    assert st.motion_allowed is False
    assert any("battery" in r for r in st.reasons)


def test_collision_latches(safety: SafetyInterlock) -> None:
    safety.set_collision(True, reason="collision_front")
    assert safety.status().motion_allowed is False
    safety.set_collision(False)
    assert safety.status().motion_allowed is False  # latched
    safety.clear_faults(acknowledge=True)
    safety.heartbeat()
    safety.control_tick()
    safety.perception_tick()
    assert safety.status().motion_allowed is True


def test_child_pet_warns_and_blocks_arm(safety: SafetyInterlock) -> None:
    safety.set_child_pet_proximity(True)
    st = safety.status()
    assert st.state == SafetyState.WARN
    assert st.motion_allowed is True
    assert st.arm_allowed is False


def test_torque_limit(safety: SafetyInterlock) -> None:
    safety.set_torque_limit_nm(5.0)
    st = safety.check_torque(12.0)
    assert st.motion_allowed is False


def test_custom_soft_limits() -> None:
    s = SafetyInterlock(soft_limits=SoftLimits(max_linear_speed_mps=0.3))
    s.heartbeat()
    s.perception_tick()
    s.control_tick()
    assert s.check_base_command(0.2, 0.0, 0.0).motion_allowed
    assert not s.check_base_command(0.5, 0.0, 0.0).motion_allowed
