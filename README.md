# Mandelbulb Viewer

A Python project for interactive 3D Mandelbulb visualization using distance estimation and ray marching.

**Status:** Phase 00 — project foundation. Rendering and GUI are not implemented yet.

## Development setup

Requires uv and Python 3.12. On Windows, verify Tkinter with `uv run python -m tkinter`.

```powershell
uv sync
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
```

The palette module contains the 17 inherited Arnold Tongue palettes and Geoz. Yikique is the default.
