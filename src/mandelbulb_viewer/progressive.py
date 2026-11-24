"""Render planning and supersampled image generation, independent of Tk."""

from dataclasses import dataclass

from PIL import Image

from mandelbulb_viewer.lighting import render_image


@dataclass(frozen=True)
class RenderPass:
    width: int
    height: int
    samples: int = 1


def plan_passes(width: int, height: int, quality: str) -> tuple[RenderPass, ...]:
    """Preserve aspect ratio and avoid redundant preview passes."""
    if width < 1 or height < 1 or quality not in ("Preview", "Normal", "High"):
        raise ValueError("Invalid render dimensions or quality")

    def fit(limit, samples=1):
        scale = min(1.0, limit / max(width, height))
        return RenderPass(max(1, round(width * scale)), max(1, round(height * scale)), samples)

    preview = fit(240)
    final = fit(
        {"Preview": 240, "Normal": 480, "High": 900}[quality], 2 if quality == "High" else 1
    )
    return (final,) if preview == final else (preview, final)


def render_pass(camera, stage: RenderPass, settings):
    """Average a regular subpixel grid for high-quality output."""
    if stage.samples not in (1, 2) or not all(
        1 <= n <= 4096 // stage.samples for n in (stage.width, stage.height)
    ):
        raise ValueError("Invalid render pass")
    rgb = render_image(
        camera, stage.width * stage.samples, stage.height * stage.samples, **settings
    )
    picture = Image.fromarray(rgb)
    if stage.samples > 1:
        picture = picture.resize((stage.width, stage.height), Image.Resampling.BOX)
    return picture
