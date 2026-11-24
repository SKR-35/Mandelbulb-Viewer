import numpy as np
import pytest

from mandelbulb_viewer.camera import Camera
from mandelbulb_viewer.gui import orbit, pan, zoom
from mandelbulb_viewer.lighting import render_image


def test_orbit():
    camera = Camera()
    other = orbit(camera, 50, 20)
    assert other.target == camera.target
    assert other.position != camera.position
    assert np.linalg.norm(other.position) == pytest.approx(np.linalg.norm(camera.position))


def test_pan():
    camera = Camera()
    other = pan(camera, 30, 20, 500)
    np.testing.assert_allclose(other.frame()[1], camera.frame()[1])
    assert other.target != camera.target


def test_zoom():
    assert zoom(Camera(), 1).fov < Camera().fov
    assert zoom(Camera(), 100).fov == 1
    assert zoom(Camera(), -100).fov == 100


@pytest.mark.parametrize("mode", ["height", "angular"])
def test_color_modes(mode):
    base = render_image(width=16, height=16)
    other = render_image(width=16, height=16, color_mode=mode, color_cycles=2)
    assert np.any(base != other)


@pytest.mark.parametrize("kwargs", [{"color_mode": "bad"}, {"ambient": -1}, {"exposure": 0}])
def test_invalid_shading(kwargs):
    with pytest.raises(ValueError):
        render_image(**kwargs)
