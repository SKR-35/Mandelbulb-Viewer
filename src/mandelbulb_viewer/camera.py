"""Perspective camera with a stable orthonormal frame."""

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Camera:
    position: tuple[float, float, float] = (3.0, 2.0, 3.0)
    target: tuple[float, float, float] = (0.0, 0.0, 0.0)
    fov: float = 40.0

    def frame(self):
        """Return origin, forward, right and up in world coordinates (Z up)."""
        origin = np.asarray(self.position, dtype=np.float64)
        target = np.asarray(self.target, dtype=np.float64)
        if any(
            v.shape != (3,) or not np.isfinite(v).all() or np.max(abs(v)) > 1e5
            for v in (origin, target)
        ):
            raise ValueError("Camera vectors must be finite 3D coordinates within +/-1e5")
        if not math.isfinite(self.fov) or not 1 <= self.fov <= 120:
            raise ValueError("Vertical FOV must be between 1 and 120 degrees")
        forward = target - origin
        length = np.linalg.norm(forward)
        if length < 1e-10:
            raise ValueError("Camera position and target must differ")
        forward /= length
        reference = np.array([0.0, 0.0, 1.0])
        if abs(forward[2]) > 0.999:
            reference = np.array([0.0, 1.0, 0.0])
        right = np.cross(forward, reference)
        right /= np.linalg.norm(right)
        up = np.cross(right, forward)
        return origin, forward, right, up
