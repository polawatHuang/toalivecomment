import pytest

from fbcollector.services.wheel.wheel_engine import WheelPhysics


def test_ease_out_cubic_bounds():
    assert WheelPhysics.ease_out_cubic(0) == 0
    assert WheelPhysics.ease_out_cubic(1) == 1


def test_ease_out_cubic_monotonic_increasing():
    values = [WheelPhysics.ease_out_cubic(t / 10) for t in range(11)]
    assert values == sorted(values)


def test_plan_spin_winner_index_within_range():
    for _ in range(50):
        plan = WheelPhysics.plan_spin(entrant_count=7)
        assert 0 <= plan.winner_index < 7


def test_plan_spin_rejects_non_positive_entrant_count():
    with pytest.raises(ValueError):
        WheelPhysics.plan_spin(entrant_count=0)


def test_angle_at_start_and_end():
    plan = WheelPhysics.plan_spin(entrant_count=5, duration_ms=1000)
    assert WheelPhysics.angle_at(0, plan) == 0
    assert WheelPhysics.angle_at(1000, plan) == pytest.approx(plan.total_rotation_degrees)


def test_angle_at_clamps_no_overshoot():
    plan = WheelPhysics.plan_spin(entrant_count=5, duration_ms=1000)
    assert WheelPhysics.angle_at(5000, plan) == pytest.approx(plan.total_rotation_degrees)
