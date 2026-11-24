import numpy as np
import pytest

from mandelbulb_viewer.camera import Camera
from mandelbulb_viewer.render import render_geometry


def test_geometry():
    result = render_geometry(width=21, height=21)
    assert result.hit.shape == (21, 21)
    assert result.hit[10, 10]
    assert not result.hit[0, 0]
    assert np.isfinite(result.depth[result.hit]).all()
    assert np.isinf(result.depth[~result.hit]).all()
    assert (result.steps > 0).all()
    assert (result.steps <= 256).all()


def test_camera_looking_away():
    result = render_geometry(Camera(position=(0, 0, 3), target=(0, 0, 4)), 3, 3)
    assert not result.hit.any()


def test_step_limit():
    result = render_geometry(width=1, height=1, max_steps=1)
    assert not result.hit[0, 0]
    assert result.steps[0, 0] == 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"width": 0},
        {"height": True},
        {"epsilon": 0},
        {"far": float("inf")},
        {"max_steps": 0},
        {"power": 1},
    ],
)
def test_invalid_settings(kwargs):
    with pytest.raises(ValueError):
        render_geometry(**kwargs)
