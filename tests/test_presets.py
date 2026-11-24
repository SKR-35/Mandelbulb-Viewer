import numpy as np
import pytest

from mandelbulb_viewer.lighting import _orbit_trap, render_image
from mandelbulb_viewer.presets import PRESETS, preset_settings


def test_trap_origin():
    assert _orbit_trap(np.zeros(3), 8.0, 20, 4.0) == 0.0


def test_trap_escaped():
    assert _orbit_trap(np.array([5.0, 0.0, 0.0]), 8.0, 20, 4.0) == 1.0


def test_trap_single_update():
    assert _orbit_trap(np.array([0.0, 0.0, -0.5]), 2.0, 1, 4.0) == pytest.approx(0.25)


@pytest.mark.parametrize("name", PRESETS)
def test_preset_render(name):
    settings = preset_settings(name)
    image = render_image(width=16, height=16, **settings)
    assert image.shape == (16, 16, 3)
    assert image.dtype == np.uint8
    assert np.any(image != [8, 10, 18])
    settings["power"] = 2.0
    assert preset_settings(name)["power"] != 2.0


def test_trap_color_differs():
    a = render_image(width=20, height=20, color_mode="orbit_trap")
    b = render_image(width=20, height=20, color_mode="radial")
    assert np.any(a != b)
