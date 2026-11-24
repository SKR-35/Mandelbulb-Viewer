import pytest
from PIL import Image

from mandelbulb_viewer.camera import Camera
from mandelbulb_viewer.export import ExportCancelled, export_scene, frame_scene
from mandelbulb_viewer.progressive import RenderPass


@pytest.mark.parametrize("mode", ["Camera Orbit", "Power Morph", "Palette Cycle", "Zoom"])
def test_loop(mode):
    camera = Camera()
    settings = {"power": 8.0, "color_offset": 0.2}
    a, s = frame_scene(camera, settings, mode, 0)
    b, t = frame_scene(camera, settings, mode, 1)
    assert a.position == pytest.approx(b.position)
    assert a.fov == pytest.approx(b.fov)
    assert s == pytest.approx(t)
    assert settings == {"power": 8.0, "color_offset": 0.2}


@pytest.mark.parametrize("suffix", ["png", "gif", "mp4"])
def test_export(tmp_path, monkeypatch, suffix):
    from mandelbulb_viewer import export

    monkeypatch.setattr(export, "render_pass", lambda *args: Image.new("RGB", (16, 16), "red"))
    path = tmp_path / f"output.{suffix}"
    events = []
    export_scene(
        path,
        Camera(),
        {},
        RenderPass(16, 16),
        fps=2,
        seconds=1,
        progress=lambda d, t: events.append((d, t)),
    )
    assert path.stat().st_size > 0
    assert events[-1] == ((1, 1) if suffix == "png" else (2, 2))
    if suffix != "mp4":
        with Image.open(path) as image:
            assert image.size == (16, 16)


def test_cancel_preserves_existing(tmp_path):
    path = tmp_path / "output.png"
    path.write_bytes(b"original")
    with pytest.raises(ExportCancelled):
        export_scene(path, Camera(), {}, RenderPass(16, 16), cancelled=lambda: True)
    assert path.read_bytes() == b"original"
    assert list(tmp_path.iterdir()) == [path]
