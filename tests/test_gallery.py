from pathlib import Path

import pytest

from mandelbulb_viewer import gallery


def test_dry_run(tmp_path, capsys):
    output = tmp_path / "gallery"
    assert gallery.main(["--output", str(output), "--dry-run"]) == 0
    assert "[18/18]" in capsys.readouterr().out
    assert not output.exists()


def test_julia_and_skip(tmp_path, monkeypatch):
    calls = []

    def export(path, camera, settings, stage, *args, **kwargs):
        calls.append(settings)
        Path(path).touch()

    monkeypatch.setattr(gallery, "export_scene", export)
    args = ["--output", str(tmp_path), "--preset", "Classic Rainbow", "--fractal", "julia"]
    gallery.main(args)
    gallery.main(args)
    assert len(calls) == 1
    assert calls[0]["fractal"] == "Julia Bulb"
    gallery.main(args + ["--overwrite"])
    assert len(calls) == 2


def test_invalid_dimensions():
    with pytest.raises(SystemExit):
        gallery.main(["--width", "4096", "--samples", "2"])
