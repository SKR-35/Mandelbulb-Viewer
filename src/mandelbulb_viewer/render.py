"""Parallel CPU ray marching; geometry only, independent of shading."""

import math
from dataclasses import dataclass

import numpy as np
from numba import njit, prange

from mandelbulb_viewer.camera import Camera
from mandelbulb_viewer.core import _estimate, estimate


@dataclass(frozen=True)
class Geometry:
    depth: np.ndarray
    hit: np.ndarray
    steps: np.ndarray


@njit(cache=True)
def _march(origin, direction, power, iterations, bailout, epsilon, max_steps, far, julia=None):
    distance = 0.0
    for step in range(1, max_steps + 1):
        x, y, z = origin + distance * direction
        value, _, _ = _estimate(x, y, z, power, iterations, bailout, julia)
        if value <= epsilon:
            return distance, True, step
        # The estimator is approximate; a conservative step reduces overshoot.
        distance += 0.7 * value
        if distance > far:
            return math.inf, False, step
    return math.inf, False, max_steps


@njit(cache=True, parallel=True)
def _render(
    origin,
    forward,
    right,
    up,
    scale,
    width,
    height,
    power,
    iterations,
    bailout,
    epsilon,
    max_steps,
    far,
    julia=None,
):
    depth = np.empty((height, width), dtype=np.float64)
    hit = np.empty((height, width), dtype=np.bool_)
    steps = np.empty((height, width), dtype=np.int32)
    for y in prange(height):
        for x in range(width):
            u = (2 * (x + 0.5) / width - 1) * width / height * scale
            v = (1 - 2 * (y + 0.5) / height) * scale
            direction = forward + u * right + v * up
            direction /= np.sqrt(np.dot(direction, direction))
            depth[y, x], hit[y, x], steps[y, x] = _march(
                origin, direction, power, iterations, bailout, epsilon, max_steps, far, julia
            )
    return depth, hit, steps


def render_geometry(
    camera: Camera | None = None,
    width: int = 320,
    height: int = 240,
    *,
    power: float = 8.0,
    iterations: int = 20,
    bailout: float = 4.0,
    epsilon: float = 0.001,
    max_steps: int = 256,
    far: float = 20.0,
    julia=None,
) -> Geometry:
    """Render depth, hit mask and step count. Misses have infinite depth."""
    if any(type(v) is not int or not 1 <= v <= 4096 for v in (width, height)):
        raise ValueError("Dimensions must be integers between 1 and 4096")
    if type(max_steps) is not int or not 1 <= max_steps <= 4096:
        raise ValueError("Maximum steps must be an integer between 1 and 4096")
    if not math.isfinite(epsilon) or not 0 < epsilon <= 0.1:
        raise ValueError("Epsilon must be positive and at most 0.1")
    if not math.isfinite(far) or not 0 < far <= 1e5:
        raise ValueError("Far distance must be positive and at most 1e5")
    estimate(0.0, 0.0, 0.0, power, iterations, bailout, julia)
    if camera is None:
        camera = Camera()
    frame = camera.frame()
    return Geometry(
        *_render(
            *frame,
            math.tan(math.radians(camera.fov) / 2),
            width,
            height,
            power,
            iterations,
            bailout,
            epsilon,
            max_steps,
            far,
            julia,
        )
    )
