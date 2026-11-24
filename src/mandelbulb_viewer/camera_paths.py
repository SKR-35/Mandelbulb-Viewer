"""One-way camera paths with conservative exterior clearance checks."""

import math
from dataclasses import replace

import numpy as np

from mandelbulb_viewer.core import estimate

CAMERA_MODES = ("Deep Zoom", "Spiral Dive", "Fractal Flythrough")


def camera_path(camera, settings, mode, phase):
    """Approach the first visible surface; optionally steer along its exterior.

    Clearance is heuristic, not a certified collision bound. Paths stop rather
    than crossing a sampled non-escaping point.
    """
    if mode not in CAMERA_MODES or not 0 <= phase <= 1:
        raise ValueError("Invalid camera path or phase")
    origin, forward, right, up = camera.frame()
    power = settings.get("power", 8.0)
    iterations = settings.get("iterations", 20)
    bailout = settings.get("bailout", 4.0)

    julia = (
        tuple(settings.get(k, v) for k, v in (("cx", 0.35), ("cy", 0.2), ("cz", 0.1)))
        if settings.get("fractal") == "Julia Bulb"
        else None
    )

    def clearance(point):
        return estimate(*point, power, iterations, bailout, julia)[0]

    if clearance(origin) <= 0.002:
        raise ValueError("Camera must start outside the fractal")
    # Locate a surface along the central ray using conservative steps.
    p = origin.copy()
    for _ in range(1024):
        d = clearance(p)
        if d <= 0.0002:
            break
        p += forward * min(0.4 * d, 0.1)
        if np.linalg.norm(p - origin) > 20:
            raise ValueError("Aim the camera at the fractal before exporting")
    else:
        raise ValueError("No surface found along camera direction")
    target = p
    length = float(np.linalg.norm(target - origin))
    end_gap = min(length, 0.008)
    gap = length * (end_gap / length) ** phase
    desired = target - forward * gap
    if mode != "Deep Zoom":
        angle = phase * 4 * math.pi
        amplitude = gap * 0.35 * math.sin(math.pi * phase)
        if mode == "Fractal Flythrough":
            amplitude = min(0.12, gap * 0.7) * math.sin(math.pi * phase)
        desired += amplitude * (math.cos(angle) * right + math.sin(angle) * up)
    # Verify the straight segment to the candidate with adaptive samples.
    delta = desired - origin
    travel = float(np.linalg.norm(delta))
    position = origin.copy()
    if travel > 0:
        direction = delta / travel
        remaining = travel
        for _ in range(4096):
            d = clearance(position)
            step = min(remaining, 0.25 * d, 0.05)
            if step <= 1e-8:
                break
            candidate = position + step * direction
            if clearance(candidate) < 0.0005:
                break
            position = candidate
            remaining -= step
            if remaining <= 1e-8:
                break
    config = dict(settings)
    config["epsilon"] = min(settings.get("epsilon", 0.001), max(0.000002, gap * 0.001))
    config["max_steps"] = max(settings.get("max_steps", 256), 512)
    return replace(camera, position=tuple(position), target=tuple(target)), config
