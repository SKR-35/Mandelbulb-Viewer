import numpy as np

from mandelbulb_viewer.camera import Camera
from mandelbulb_viewer.export import suggested_filename
from mandelbulb_viewer.lighting import _cached_geometry, _cached_shading, render_image
from mandelbulb_viewer.progressive import RenderPass


def test_filename():
    assert (
        suggested_filename(
            {"palette": "Geoz", "power": 8.5}, RenderPass(480, 480), ".GIF", "Camera Orbit", 12, 4
        )
        == "mandelbulb_geoz_p8.5_it20_radial_480x480_camera-orbit_12fps_4s_ss1.gif"
    )


def test_cache():
    _cached_geometry.cache_clear()
    _cached_shading.cache_clear()
    first = render_image(width=12, height=12)
    second = render_image(width=12, height=12, palette="Geoz")
    assert _cached_shading.cache_info().hits == 1
    assert not np.array_equal(first, second)
    render_image(width=12, height=12, ambient=0.7)
    assert _cached_geometry.cache_info().hits == 1
    render_image(Camera(fov=35), width=12, height=12)
    assert _cached_geometry.cache_info().misses == 2
