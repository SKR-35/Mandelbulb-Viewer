"""Named, reproducible fractal and shading configurations."""

PRESETS = {
    "Classic Rainbow": dict(
        power=8.0,
        palette="Yikique",
        color_mode="angular",
        color_cycles=2.0,
        color_offset=0.0,
        gamma=0.85,
        ambient=0.5,
        ao_strength=0.5,
        exposure=1.3,
        iterations=20,
    ),
    "Golden Coral": dict(
        power=8.0,
        palette="Geoz",
        color_mode="orbit_trap",
        color_cycles=2.0,
        color_offset=0.1,
        gamma=0.8,
        ambient=0.5,
        ao_strength=0.5,
        exposure=1.4,
        iterations=24,
    ),
    "Pearl Sculpture": dict(
        power=8.0,
        palette="Pearl",
        color_mode="height",
        color_cycles=1.0,
        color_offset=0.0,
        gamma=0.7,
        ambient=0.6,
        ao_strength=0.4,
        exposure=1.5,
        iterations=24,
    ),
    "Jade Bloom": dict(
        power=6.0,
        palette="Jade",
        color_mode="orbit_trap",
        color_cycles=1.5,
        color_offset=0.1,
        gamma=0.8,
        ambient=0.5,
        ao_strength=0.5,
        exposure=1.4,
        iterations=24,
    ),
}


def preset_settings(name):
    """Return an independent copy of a named configuration."""
    return PRESETS[name].copy()
