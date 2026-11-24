import numpy as np
import pytest

from mandelbulb_viewer import progressive
from mandelbulb_viewer.progressive import RenderPass, plan_passes, render_pass


@pytest.mark.parametrize(
    "quality,limit,samples", [("Preview", 240, 1), ("Normal", 480, 1), ("High", 900, 2)]
)
def test_plan(quality, limit, samples):
    passes = plan_passes(1200, 600, quality)
    assert passes[0] == RenderPass(240, 120)
    assert passes[-1] == RenderPass(limit, limit // 2, samples)


def test_small_canvas():
    assert plan_passes(80, 40, "Normal") == (RenderPass(80, 40),)


@pytest.mark.parametrize("args", [(0, 10, "High"), (10, 0, "Normal"), (10, 10, "bad")])
def test_invalid_plan(args):
    with pytest.raises(ValueError):
        plan_passes(*args)


def test_supersampling(monkeypatch):
    def fake(camera, width, height, **settings):
        assert (width, height) == (4, 2)
        assert settings == {"power": 8}
        rgb = np.zeros((height, width, 3), dtype=np.uint8)
        rgb[:, 1::2] = 200
        return rgb

    monkeypatch.setattr(progressive, "render_image", fake)
    image = render_pass(None, RenderPass(2, 1, 2), {"power": 8})
    assert image.size == (2, 1)
    assert np.all(np.asarray(image) == 100)


def test_invalid_samples():
    with pytest.raises(ValueError):
        render_pass(None, RenderPass(2, 2, 3), {})


def test_stale_result_is_not_displayed():
    from concurrent.futures import Future
    from types import SimpleNamespace
    from unittest.mock import Mock

    from mandelbulb_viewer.gui import Viewer

    viewer = Viewer.__new__(Viewer)
    viewer.closed = False
    viewer.generation = 2
    viewer.pending = False
    viewer.timer = None
    viewer.canvas = Mock()
    viewer.status = Mock()
    viewer.future = Future()
    viewer.future.set_result(SimpleNamespace(size=(10, 10)))
    viewer.poll(1, None, {}, (RenderPass(10, 10),))
    viewer.canvas.assert_not_called()
    viewer.canvas.delete.assert_not_called()
    viewer.status.set.assert_not_called()
    assert viewer.future is None
