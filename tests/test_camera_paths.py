import numpy as np
import pytest

from mandelbulb_viewer.camera import Camera
from mandelbulb_viewer.camera_paths import CAMERA_MODES, camera_path
from mandelbulb_viewer.core import estimate


@pytest.mark.parametrize("mode", CAMERA_MODES)
def test_approach(mode):
    camera = Camera()
    settings = {"power": 8.0}
    start, _ = camera_path(camera, settings, mode, 0.0)
    end, config = camera_path(camera, settings, mode, 1.0)
    assert start.position == pytest.approx(camera.position)
    assert np.linalg.norm(np.array(end.position) - end.target) < 0.05
    assert estimate(*end.position)[0] > 0
    assert config["epsilon"] < 0.001
    assert settings == {"power": 8.0}


def test_camera_inside():
    with pytest.raises(ValueError):
        camera_path(Camera(position=(0.0, 0.0, 0.0), target=(1.0, 0.0, 0.0)), {}, "Deep Zoom", 0.0)
