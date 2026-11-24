import numpy as np
import pytest

from mandelbulb_viewer.camera import Camera


@pytest.mark.parametrize("position", [(3, 2, 3), (0, 0, 3), (0, 0, -3)])
def test_frame(position):
    origin, forward, right, up = Camera(position=position).frame()
    np.testing.assert_allclose(origin, position)
    basis = np.array([forward, right, up])
    np.testing.assert_allclose(basis @ basis.T, np.eye(3), atol=1e-12)
    np.testing.assert_allclose(forward, -origin / np.linalg.norm(origin))


@pytest.mark.parametrize(
    "camera",
    [
        Camera(position=(0, 0, 0)),
        Camera(fov=0),
        Camera(position=(float("nan"), 0, 0)),
        Camera(fov=121),
    ],
)
def test_invalid_camera(camera):
    with pytest.raises(ValueError):
        camera.frame()
