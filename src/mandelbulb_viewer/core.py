"""Mandelbulb escape-time and exterior distance estimation kernels."""

import math

from numba import njit

DEFAULT_POWER = 8.0
DEFAULT_ITERATIONS = 20
DEFAULT_BAILOUT = 4.0


@njit(cache=True)
def _estimate(x, y, z, power, max_iterations, bailout):
    # Starting at c skips the trivial first iteration from the origin.
    zx, zy, zz = x, y, z
    derivative = 1.0
    for iteration in range(max_iterations + 1):
        radius = math.sqrt(zx * zx + zy * zy + zz * zz)
        if radius > bailout:
            return 0.5 * radius * math.log(radius) / derivative, iteration, True
        if iteration == max_iterations:
            break
        if radius == 0.0:
            zx, zy, zz = x, y, z
            derivative = 1.0
            continue
        theta = math.acos(max(-1.0, min(1.0, zz / radius))) * power
        phi = math.atan2(zy, zx) * power
        derivative = power * radius ** (power - 1.0) * derivative + 1.0
        magnitude = radius**power
        zx = magnitude * math.sin(theta) * math.cos(phi) + x
        zy = magnitude * math.sin(theta) * math.sin(phi) + y
        zz = magnitude * math.cos(theta) + z
    # Non-escape is not proof of membership; zero is a rendering convention.
    return 0.0, max_iterations, False


def estimate(
    x: float,
    y: float,
    z: float,
    power: float = DEFAULT_POWER,
    max_iterations: int = DEFAULT_ITERATIONS,
    bailout: float = DEFAULT_BAILOUT,
) -> tuple[float, int, bool]:
    """Return distance estimate, updates from c, and escape status.

    Coordinates are limited to a generous rendering domain to avoid overflow.
    The internal kernel assumes validated parameters and finite coordinates.
    """
    if not all(math.isfinite(v) and abs(v) <= 1e6 for v in (x, y, z)):
        raise ValueError("Coordinates must be finite and within +/-1e6")
    if not math.isfinite(power) or not 2.0 <= power <= 16.0:
        raise ValueError("Power must be between 2 and 16")
    if type(max_iterations) is not int or not 1 <= max_iterations <= 256:
        raise ValueError("Iterations must be an integer between 1 and 256")
    if not math.isfinite(bailout) or not 2.0 <= bailout <= 16.0:
        raise ValueError("Bailout must be between 2 and 16")
    return _estimate(float(x), float(y), float(z), float(power), max_iterations, float(bailout))


def distance_estimate(x: float, y: float, z: float, **kwargs) -> float:
    """Return only the exterior distance estimate (zero for non-escape)."""
    return estimate(x, y, z, **kwargs)[0]
