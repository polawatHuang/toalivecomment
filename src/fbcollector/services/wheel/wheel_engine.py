"""Pure physics/easing math for the Lucky Wheel - no Tkinter dependency, fully unit-testable."""

import random
from dataclasses import dataclass

from fbcollector.constants import WHEEL_DEFAULT_DURATION_MS, WHEEL_MIN_FULL_ROTATIONS

_secure_random = random.SystemRandom()


@dataclass(frozen=True, slots=True)
class WheelSpinPlan:
    """Describes one spin: how far to rotate, how long it takes, and who wins."""

    total_rotation_degrees: float
    duration_ms: int
    winner_index: int


class WheelPhysics:
    """Stateless helpers for planning and animating a spin."""

    @staticmethod
    def plan_spin(
        entrant_count: int,
        min_full_rotations: int = WHEEL_MIN_FULL_ROTATIONS,
        duration_ms: int = WHEEL_DEFAULT_DURATION_MS,
    ) -> WheelSpinPlan:
        if entrant_count <= 0:
            raise ValueError("entrant_count must be positive")

        winner_index = _secure_random.randrange(entrant_count)
        segment_degrees = 360.0 / entrant_count
        # land the pointer (fixed at the top, angle 0) in the middle of the winner's segment
        winner_center = winner_index * segment_degrees + segment_degrees / 2
        target_within_circle = (360.0 - winner_center) % 360.0
        total_rotation = min_full_rotations * 360.0 + target_within_circle
        return WheelSpinPlan(
            total_rotation_degrees=total_rotation, duration_ms=duration_ms, winner_index=winner_index
        )

    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """t in [0, 1] -> eased progress in [0, 1], decelerating towards the end."""
        clamped = min(1.0, max(0.0, t))
        return 1 - pow(1 - clamped, 3)

    @staticmethod
    def angle_at(elapsed_ms: int, plan: WheelSpinPlan) -> float:
        t = min(1.0, elapsed_ms / plan.duration_ms) if plan.duration_ms > 0 else 1.0
        return plan.total_rotation_degrees * WheelPhysics.ease_out_cubic(t)
