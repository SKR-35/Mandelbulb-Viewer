# Mandelbulb Viewer

Interactive desktop visualization of the three-dimensional Mandelbulb fractal using CPU ray marching and distance estimation.

## Features

- Perspective camera with orbit, pan and field-of-view zoom.
- Adjustable fractal power and iteration count.
- 18 color palettes with radial, height, angular and spherical orbit-trap mapping.
- 18 named fractal and shading presets, one for each palette.
- Adjustable lighting, ambient occlusion, gamma and exposure.
- Background rendering with progressive previews and optional 2×2 supersampling in High quality mode.

## Installation

Requires Python 3.12, uv and Tkinter. From the repository root:

```sh
uv sync
uv run python -m mandelbulb_viewer
```

## Controls

Left-drag to orbit, right-drag to pan, and scroll to zoom. Use the side panel to adjust fractal and shading parameters. Preview quality renders at up to 240 pixels on the longest edge; Normal at up to 480; High at up to 900 with four subpixel samples per output pixel. Images are scaled to fit the canvas. Initial rendering may take longer due to Numba compilation.

## Export

Use the Export toolbar button or menu to save PNG images or GIF/MP4 animations. Select dimensions, frame rate, duration and sampling independently of the canvas. Animation modes include camera orbit, power morph, palette cycling and zoom. MP4 requires even dimensions. Cancellation takes effect between frames. Suggested filenames include scene and export parameters.

## Rendering method

The renderer uses a spherical-coordinate power iteration and an approximate distance estimator. Surface normals are estimated by finite differences; lighting uses diffuse and Blinn–Phong specular terms with approximate ambient occlusion. Rendering runs on the CPU using Numba parallel kernels. The toolbar controls the worker thread count. The most recent geometry and shading fields are cached for compatible render requests, including palette-cycle animation frames.

## Development

```sh
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

## License

Apache-2.0. See [LICENSE](LICENSE).

### Advanced camera animations

Deep Zoom moves the camera toward the first surface along its viewing direction.
Spiral Dive adds a lateral spiral. Fractal Flythrough is an experimental exterior
approach with lateral steering; it does not guarantee traversal of arbitrary
cavities. Aim the camera at the desired region before exporting. These modes
are one-way paths, not seamless loops. Surface clearance is approximate.

### Julia Bulb

Select **Julia Bulb** in the fractal selector and adjust Cx, Cy and Cz in the toolbar. The fixed three-dimensional constant replaces the spatially varying Mandelbulb constant. Export supports Julia Bulb Morph (fixed camera) and Julia Bulb Orbit (moving camera). Both follow periodic parameter paths. Distance estimation is approximate; some parameter combinations may produce disconnected or poorly resolved surfaces.
