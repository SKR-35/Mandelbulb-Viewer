import math

import numpy as np
import pytest

from mandelbulb_viewer.camera import Camera
from mandelbulb_viewer.core import estimate
from mandelbulb_viewer.export import JULIA_MODES, frame_scene
from mandelbulb_viewer.lighting import render_image


def test_zero_constant():
    assert not estimate(0.5, 0, 0, julia=(0.0, 0.0, 0.0))[2]
    assert estimate(2, 0, 0, julia=(0.0, 0.0, 0.0))[2]
    assert estimate(2, 0, 0, julia=(0.0, 0.0, 0.0))[0] == pytest.approx(math.log(2))


@pytest.mark.parametrize("mode", JULIA_MODES)
def test_julia_loop(mode):
    camera = Camera()
    settings = {"cx": 0.35}
    a, first = frame_scene(camera, settings, mode, 0)
    b, last = frame_scene(camera, settings, mode, 1)
    assert a.position == pytest.approx(b.position)
    assert first["fractal"] == last["fractal"] == "Julia Bulb"
    for key in ("cx", "cy", "cz"):
        assert first[key] == pytest.approx(last[key])
    assert settings == {"cx": 0.35}


def test_julia_render():
    settings = dict(width=24, height=24, fractal="Julia Bulb", color_mode="orbit_trap")
    a = render_image(**settings)
    b = render_image(**settings, cx=0.65)
    assert a.shape == (24, 24, 3)
    assert np.any(a != b)
    assert np.any(a != [8, 10, 18])


def test_invalid_constant():
    with pytest.raises(ValueError):
        estimate(0, 0, 0, julia=(float("nan"), 0, 0))
