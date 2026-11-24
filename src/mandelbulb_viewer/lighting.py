"""Surface shading for the distance-estimated Mandelbulb."""

import math
from functools import lru_cache

import numpy as np
from numba import njit, prange

from mandelbulb_viewer.camera import Camera
from mandelbulb_viewer.core import _estimate, estimate
from mandelbulb_viewer.palettes import DEFAULT_PALETTE, colorize
from mandelbulb_viewer.render import render_geometry


@njit(cache=True)
def _distance(p, power, iterations, bailout):
    return _estimate(p[0], p[1], p[2], power, iterations, bailout)[0]


@njit(cache=True)
def _normal(p, direction, delta, power, iterations, bailout):
    gradient = np.empty(3)
    for axis in range(3):
        offset = np.zeros(3)
        offset[axis] = delta
        gradient[axis] = _distance(p + offset, power, iterations, bailout) - _distance(
            p - offset, power, iterations, bailout
        )
    length = np.sqrt(np.dot(gradient, gradient))
    if length < 1e-15:
        return -direction
    return gradient / length


@njit(cache=True)
def _occlusion(p, normal, epsilon, power, iterations, bailout):
    deficit = 0.0
    for i in range(1, 6):
        distance = max(4 * epsilon, 0.015) * i
        actual = _distance(p + normal * distance, power, iterations, bailout)
        deficit += max(0.0, 1.0 - actual / distance) * 0.5**i
    return max(0.25, 1.0 - 0.8 * deficit)


@njit(cache=True)
def _orbit_trap(p, power, iterations, bailout):
    # Minimum distance of the orbit to the origin (a spherical trap).
    x, y, z = p
    zx, zy, zz = x, y, z
    trap = math.sqrt(x * x + y * y + z * z)
    for i in range(iterations + 1):
        r = math.sqrt(zx * zx + zy * zy + zz * zz)
        trap = min(trap, r)
        if r > bailout or r == 0.0 or i == iterations:
            break
        theta = math.acos(max(-1.0, min(1.0, zz / r))) * power
        phi = math.atan2(zy, zx) * power
        magnitude = r**power
        zx = magnitude * math.sin(theta) * math.cos(phi) + x
        zy = magnitude * math.sin(theta) * math.sin(phi) + y
        zz = magnitude * math.cos(theta) + z
    return min(1.0, trap)


@njit(cache=True, parallel=True)
def _shade(
    depth,
    hit,
    origin,
    forward,
    right,
    up,
    scale,
    power,
    iterations,
    bailout,
    epsilon,
    mode,
    ambient,
    ao_strength,
):
    height, width = hit.shape
    field = np.zeros((height, width))
    illumination = np.zeros_like(field)
    highlights = np.zeros_like(field)
    light = -forward + 0.65 * up - 0.45 * right
    light /= np.sqrt(np.dot(light, light))
    for y in prange(height):
        for x in range(width):
            if not hit[y, x]:
                continue
            u = (2 * (x + 0.5) / width - 1) * width / height * scale
            v = (1 - 2 * (y + 0.5) / height) * scale
            direction = forward + u * right + v * up
            direction /= np.sqrt(np.dot(direction, direction))
            p = origin + depth[y, x] * direction
            normal = _normal(p, direction, epsilon, power, iterations, bailout)
            ao = _occlusion(p, normal, epsilon, power, iterations, bailout)
            diffuse = max(0.0, np.dot(normal, light))
            half = light - direction
            half /= np.sqrt(np.dot(half, half))
            ao = 1.0 - ao_strength * (1.0 - ao)
            illumination[y, x] = (ambient + (1.0 - ambient) * diffuse) * ao
            highlights[y, x] = 0.25 * max(0.0, np.dot(normal, half)) ** 32 * ao
            # World-space radius keeps surface colors stable during camera orbits.
            if mode == 1:
                field[y, x] = min(1.0, max(0.0, (p[2] + 1.2) / 2.4))
            elif mode == 2:
                field[y, x] = (math.atan2(p[1], p[0]) + math.pi) / (2 * math.pi)
            elif mode == 3:
                field[y, x] = _orbit_trap(p, power, iterations, bailout)
            else:
                field[y, x] = min(1.0, max(0.0, (np.sqrt(np.dot(p, p)) - 0.45) / 0.95))
    return field, illumination, highlights


@lru_cache(maxsize=1)
def _cached_geometry(camera, width, height, power, iterations, bailout, epsilon, max_steps, far):
    return render_geometry(
        camera,
        width,
        height,
        power=power,
        iterations=iterations,
        bailout=bailout,
        epsilon=epsilon,
        max_steps=max_steps,
        far=far,
    )


@lru_cache(maxsize=1)
def _cached_shading(
    camera,
    width,
    height,
    power,
    iterations,
    bailout,
    epsilon,
    max_steps,
    far,
    mode,
    ambient,
    ao_strength,
):
    geometry = _cached_geometry(
        camera, width, height, power, iterations, bailout, epsilon, max_steps, far
    )
    field, illumination, highlights = _shade(
        geometry.depth,
        geometry.hit,
        *camera.frame(),
        math.tan(math.radians(camera.fov) / 2),
        power,
        iterations,
        bailout,
        epsilon,
        mode,
        ambient,
        ao_strength,
    )
    return geometry.hit, field, illumination, highlights


def render_image(
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
    palette: str = DEFAULT_PALETTE,
    gamma: float = 1.0,
    color_mode: str = "radial",
    color_cycles: float = 1.0,
    color_offset: float = 0.0,
    ambient: float = 0.4,
    ao_strength: float = 0.65,
    exposure: float = 1.2,
) -> np.ndarray:
    """Render an RGB uint8 image; gamma controls palette mapping."""
    if camera is None:
        camera = Camera()
    # Validate palette and gamma before expensive geometry work.
    colorize(np.zeros((1, 1)), palette, gamma)
    estimate(0.0, 0.0, 0.0, power, iterations, bailout)
    modes = ("radial", "height", "angular", "orbit_trap")
    if color_mode not in modes:
        raise ValueError("Unknown color mode")
    for value, low, high in (
        (color_cycles, 0.1, 10),
        (color_offset, 0, 1),
        (ambient, 0, 1),
        (ao_strength, 0, 1),
        (exposure, 0.1, 3),
    ):
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError("Invalid shading parameter")
    hit, field, illumination, highlights = _cached_shading(
        camera,
        width,
        height,
        power,
        iterations,
        bailout,
        epsilon,
        max_steps,
        far,
        modes.index(color_mode),
        ambient,
        ao_strength,
    )
    if color_cycles != 1 or color_offset != 0:
        field = (field * color_cycles + color_offset) % 1.0
    rgb = colorize(field, palette, gamma).astype(np.float64)
    rgb = rgb * illumination[..., None] + 255 * highlights[..., None]
    rgb *= exposure
    rgb[~hit] = (8, 10, 18)
    return np.rint(np.clip(rgb, 0, 255)).astype(np.uint8)
