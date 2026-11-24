import numpy as np
import pytest

from mandelbulb_viewer.camera import Camera
from mandelbulb_viewer.lighting import _normal, _occlusion, render_image
from mandelbulb_viewer.render import render_geometry


def test_normal_exterior():
    normal = _normal(np.array([5.0, 0.0, 0.0]), np.array([-1.0, 0.0, 0.0]), 0.001, 8.0, 20, 4.0)
    np.testing.assert_allclose(normal, [1.0, 0.0, 0.0], atol=1e-6)


def test_normal_fallback():
    direction = np.array([0.0, 0.0, -1.0])
    np.testing.assert_allclose(_normal(np.zeros(3), direction, 0.001, 8.0, 20, 4.0), -direction)


def test_occlusion_bounds():
    value = _occlusion(np.array([1.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]), 0.001, 8.0, 20, 4.0)
    assert 0.25 <= value <= 1.0


def test_image_geometry_and_palette():
    geometry = render_geometry(width=32, height=24)
    image = render_image(width=32, height=24)
    assert image.shape == (24, 32, 3)
    assert image.dtype == np.uint8
    assert geometry.hit.any() and (~geometry.hit).any()
    assert np.all(image[~geometry.hit] == [8, 10, 18])
    assert np.unique(image[geometry.hit], axis=0).shape[0] > 5
    other = render_image(width=32, height=24, palette="Geoz")
    assert np.any(image[geometry.hit] != other[geometry.hit])
    np.testing.assert_array_equal(image, render_image(width=32, height=24))


def test_background_only():
    image = render_image(Camera(target=(6.0, 4.0, 6.0)), width=8, height=8)
    assert np.all(image == [8, 10, 18])


@pytest.mark.parametrize("kwargs", [{"gamma": 0}, {"palette": "missing"}, {"width": 0}])
def test_invalid_settings(kwargs):
    with pytest.raises(ValueError):
        render_image(**kwargs)
