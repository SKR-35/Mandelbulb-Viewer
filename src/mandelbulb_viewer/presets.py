"""Named, reproducible fractal and shading configurations."""


def _scene(
    palette,
    power,
    color_mode,
    color_cycles,
    color_offset,
    gamma,
    ambient,
    ao_strength,
    exposure,
    iterations=24,
):
    return dict(
        palette=palette,
        power=power,
        color_mode=color_mode,
        color_cycles=color_cycles,
        color_offset=color_offset,
        gamma=gamma,
        ambient=ambient,
        ao_strength=ao_strength,
        exposure=exposure,
        iterations=iterations,
    )


PRESETS = {
    "Classic Rainbow": _scene("Yikique", 8.0, "angular", 2.0, 0.0, 0.85, 0.5, 0.5, 1.3, 20),
    "Golden Coral": _scene("Geoz", 8.0, "orbit_trap", 2.0, 0.1, 0.8, 0.5, 0.5, 1.4),
    "Pearl Sculpture": _scene("Pearl", 8.0, "height", 1.0, 0.0, 0.7, 0.6, 0.4, 1.5),
    "Jade Bloom": _scene("Jade", 6.0, "orbit_trap", 1.5, 0.1, 0.8, 0.5, 0.5, 1.4),
    "Plasma Nebula": _scene("plasma", 9.0, "height", 1.0, 0.0, 0.7, 0.55, 0.45, 1.35),
    "Viridian Crown": _scene("viridis", 7.0, "angular", 1.5, 0.15, 0.85, 0.55, 0.5, 1.4),
    "Magma Cathedral": _scene("magma", 10.0, "height", 1.0, 0.0, 0.65, 0.6, 0.45, 1.4),
    "Inferno Forge": _scene("inferno", 8.0, "radial", 1.4, 0.1, 0.65, 0.55, 0.5, 1.4),
    "Turbo Spectrum": _scene("turbo", 9.0, "angular", 2.0, 0.2, 0.95, 0.5, 0.45, 1.2),
    "Cividis Relic": _scene("cividis", 6.0, "height", 1.0, 0.0, 0.8, 0.6, 0.4, 1.4),
    "Twilight Dream": _scene("twilight", 8.0, "angular", 2.0, 0.25, 1.0, 0.6, 0.45, 1.35),
    "Sunset Blossom": _scene("SoftSunset", 5.0, "height", 1.0, 0.0, 0.8, 0.55, 0.4, 1.25),
    "Terrestrial Sky": _scene("EarthAndSky", 7.0, "height", 1.0, 0.0, 0.85, 0.55, 0.45, 1.25),
    "Ocean Reef": _scene("Seashore", 9.0, "orbit_trap", 1.5, 0.2, 0.75, 0.6, 0.45, 1.4),
    "Emerald Canopy": _scene("Forest", 6.0, "radial", 1.0, 0.0, 0.75, 0.55, 0.5, 1.3),
    "Fire and Ice": _scene("HotAndCold", 8.0, "angular", 1.5, 0.15, 1.0, 0.55, 0.45, 1.25),
    "Pastel Porcelain": _scene("Pastel", 5.0, "angular", 2.0, 0.1, 1.0, 0.5, 0.55, 1.1),
    "Obsidian Relief": _scene("Grayscale", 10.0, "height", 1.0, 0.0, 0.65, 0.65, 0.4, 1.5),
}


def preset_settings(name):
    """Return an independent copy of a named configuration."""
    return PRESETS[name].copy()
