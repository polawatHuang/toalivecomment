"""Pure particle-physics stepper for confetti/firework effects.

Deliberately simple (gravity + linear fade via shrinking size, since Canvas has no real
alpha channel) - explicitly scoped as best-effort visual polish, not physically exact.
Rendering is a thin loop in ``WheelWindow`` that calls ``step()`` then draws small ovals.
"""

import random
from dataclasses import dataclass, field

_GRAVITY = 480.0  # px/s^2
_COLORS = ("#6C5CE7", "#00d2ff", "#f5b942", "#ff5c5c", "#2ecc71", "#ff8fd6")


@dataclass(slots=True)
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    color: str
    size: float
    life: float  # seconds remaining

    @property
    def is_alive(self) -> bool:
        return self.life > 0 and self.size > 0.5


class ParticleSystem:
    """Owns a list of particles and steps them forward in time."""

    def __init__(self) -> None:
        self._particles: list[Particle] = []

    @property
    def particles(self) -> list[Particle]:
        return self._particles

    def spawn_burst(self, origin: tuple[float, float], count: int = 80) -> None:
        ox, oy = origin
        for _ in range(count):
            angle = random.uniform(0, 6.283185307)
            speed = random.uniform(80, 320)
            self._particles.append(
                Particle(
                    x=ox,
                    y=oy,
                    vx=speed * random.uniform(-1, 1) * 0.5 + speed * (0.5 * (1 if angle > 3.14 else -1)),
                    vy=-abs(speed * random.uniform(0.5, 1.0)),
                    color=random.choice(_COLORS),
                    size=random.uniform(4, 9),
                    life=random.uniform(1.2, 2.4),
                )
            )

    def step(self, dt: float) -> None:
        for particle in self._particles:
            particle.vy += _GRAVITY * dt
            particle.x += particle.vx * dt
            particle.y += particle.vy * dt
            particle.life -= dt
            particle.size -= dt * 2.0
        self._particles = [p for p in self._particles if p.is_alive]

    def clear(self) -> None:
        self._particles.clear()
