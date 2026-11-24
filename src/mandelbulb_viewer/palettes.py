"""RGB palettes for Mandelbulb surface color mapping."""

from __future__ import annotations

import numpy as np

# Original Julia Set Viewer palette ordering, with Yikique inserted second.
# Named matplotlib palettes are sampled into discrete RGB stops at import time.
DEFAULT_PALETTE = "Yikique"

CUSTOM_STOPS = {
    "Geoz": (
        "#350020",
        "#a50046",
        "#ff286b",
        "#ff7850",
        "#ffbf00",
        "#fff36b",
        "#fff9d6",
    ),
    "Jade": ("#020b08", "#073b2a", "#0b6b4f", "#13a777", "#62d6a7", "#d8fff0"),
    "Yikique": (
        "#08051c",
        "#25145c",
        "#3435c4",
        "#087bea",
        "#00d5e9",
        "#06e7a0",
        "#8ff03b",
        "#f9ec26",
        "#ff9a22",
        "#f43d54",
        "#ad1b8d",
        "#08051c",
    ),
    "Pearl": ("#101214", "#34383d", "#6f747a", "#b8bcc1", "#ece9e2", "#fffdf7"),
    "SoftSunset": ("#2b1055", "#6a0572", "#ff6f91", "#ffc15e", "#ffe29a"),
    "EarthAndSky": ("#1a2a6c", "#28a0b0", "#84ffc9", "#f0f3bd", "#ffd166"),
    "Seashore": ("#001219", "#005f73", "#0a9396", "#94d2bd", "#e9d8a6"),
    "Forest": ("#0b3d0b", "#236e3c", "#4caf50", "#a8e6cf", "#f1f8e9"),
    "HotAndCold": ("#313695", "#4575b4", "#74add1", "#abd9e9", "#fee090", "#f46d43", "#d73027"),
    "Pastel": ("#b3e5fc", "#c5cae9", "#e1bee7", "#f8bbd0", "#ffe0b2", "#dcedc8"),
    "Grayscale": ("#0a0a0a", "#2f2f2f", "#5e5e5e", "#9a9a9a", "#cccccc", "#f2f2f2"),
}

ORDER = (
    "Jade",
    "Yikique",
    "Pearl",
    "plasma",
    "viridis",
    "magma",
    "inferno",
    "turbo",
    "cividis",
    "twilight",
    "SoftSunset",
    "EarthAndSky",
    "Seashore",
    "Forest",
    "HotAndCold",
    "Pastel",
    "Grayscale",
    "Geoz",
)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    return tuple(int(hex_color[index : index + 2], 16) for index in (1, 3, 5))


def _matplotlib_stops(name: str) -> tuple[tuple[int, int, int], ...]:
    from matplotlib import colormaps

    cmap = colormaps[name]
    return tuple(
        tuple(int(round(channel * 255)) for channel in cmap(i / 15)[:3]) for i in range(16)
    )


PALETTES: dict[str, tuple[tuple[int, int, int], ...]] = {
    name: tuple(_hex_to_rgb(color) for color in CUSTOM_STOPS[name])
    if name in CUSTOM_STOPS
    else _matplotlib_stops(name)
    for name in ORDER
}


def colorize(values: np.ndarray, palette: str = DEFAULT_PALETTE, gamma: float = 1.0) -> np.ndarray:
    """Map a normalized [0, 1] field to a uint8 RGB array."""
    if palette not in PALETTES:
        raise ValueError(f"Unknown palette: {palette}")
    if not np.isfinite(gamma) or gamma <= 0:
        raise ValueError("gamma must be finite and positive")
    data = np.asarray(values, dtype=np.float64)
    if data.ndim != 2 or not np.isfinite(data).all():
        raise ValueError("values must be a finite 2D array")
    data = np.clip(data, 0.0, 1.0) ** gamma
    stops = np.asarray(PALETTES[palette], dtype=np.float64)
    position = data * (len(stops) - 1)
    lower = np.minimum(position.astype(np.intp), len(stops) - 2)
    weight = (position - lower)[..., None]
    return np.rint(stops[lower] * (1 - weight) + stops[lower + 1] * weight).astype(np.uint8)
