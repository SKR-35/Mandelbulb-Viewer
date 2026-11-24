"""Frame-by-frame image and animation export with atomic output replacement."""

import math
import os
import tempfile
from dataclasses import replace
from pathlib import Path

from PIL import Image

from mandelbulb_viewer.progressive import render_pass


class ExportCancelled(Exception):
    """Export was cancelled before publication."""


def frame_scene(camera, settings, mode, phase):
    """Return independent scene settings for a normalized loop phase."""
    settings = dict(settings)
    wave = (1 - math.cos(2 * math.pi * phase)) / 2
    if mode == "Camera Orbit":
        x, y, z = (a - b for a, b in zip(camera.position, camera.target, strict=True))
        angle = 2 * math.pi * phase
        offset = (
            x * math.cos(angle) - y * math.sin(angle),
            x * math.sin(angle) + y * math.cos(angle),
            z,
        )
        camera = replace(
            camera, position=tuple(a + b for a, b in zip(camera.target, offset, strict=True))
        )
    elif mode == "Power Morph":
        power = settings.get("power", 8.0)
        settings["power"] = power + (min(16, power + 2) - power if power < 16 else -2) * wave
    elif mode == "Palette Cycle":
        settings["color_offset"] = (settings.get("color_offset", 0) + phase) % 1
    elif mode == "Zoom":
        camera = replace(camera, fov=max(1, camera.fov * (1 - 0.65 * wave)))
    else:
        raise ValueError("Unknown animation mode")
    return camera, settings


def export_scene(
    path,
    camera,
    settings,
    stage,
    mode="Camera Orbit",
    fps=12,
    seconds=4,
    cancelled=lambda: False,
    progress=lambda done, total: None,
):
    """Render to a temporary file; publish only after successful completion."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in (".png", ".gif", ".mp4"):
        raise ValueError("Expected PNG, GIF or MP4")
    if not 1 <= fps <= 60 or not 1 <= seconds <= 120:
        raise ValueError("Invalid frame rate or duration")
    total = 1 if suffix == ".png" else round(fps * seconds)
    if suffix == ".mp4" and (stage.width % 2 or stage.height % 2):
        raise ValueError("MP4 dimensions must be even")
    # Pillow retains GIF frames in memory; bound the worst-case RGB allocation.
    if suffix == ".gif" and total * stage.width * stage.height * 3 > 256 * 1024**2:
        raise ValueError("GIF too large; reduce resolution or duration, or use MP4")
    fd, temporary = tempfile.mkstemp(suffix=suffix, dir=path.parent)
    os.close(fd)
    frames = []
    writer = None
    try:
        if suffix == ".mp4":
            import imageio.v2 as imageio

            writer = imageio.get_writer(
                temporary, fps=fps, codec="libx264", macro_block_size=1, pixelformat="yuv420p"
            )
        for i in range(total):
            if cancelled():
                raise ExportCancelled()
            cam, config = (
                (camera, settings)
                if suffix == ".png"
                else frame_scene(camera, settings, mode, i / total)
            )
            picture = render_pass(cam, stage, config)
            if suffix == ".png":
                picture.save(temporary)
            elif writer is not None:
                import numpy as np

                writer.append_data(np.asarray(picture))
            else:
                frames.append(picture.convert("P", palette=Image.Palette.ADAPTIVE))
            progress(i + 1, total)
        if writer is not None:
            writer.close()
            writer = None
        if frames:
            durations = [
                round((i + 1) * 100 / fps) * 10 - round(i * 100 / fps) * 10 for i in range(total)
            ]
            frames[0].save(
                temporary,
                save_all=True,
                append_images=frames[1:],
                duration=durations if len(frames) > 1 else durations[0],
                loop=0,
                disposal=2,
            )
        if cancelled():
            raise ExportCancelled()
        os.replace(temporary, path)
    finally:
        try:
            if writer is not None:
                writer.close()
        finally:
            Path(temporary).unlink(missing_ok=True)
