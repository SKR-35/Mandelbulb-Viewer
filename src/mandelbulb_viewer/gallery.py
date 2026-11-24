"""Generate reproducible preset galleries from the command line."""

import argparse
import time
from pathlib import Path

from mandelbulb_viewer.camera import Camera
from mandelbulb_viewer.export import JULIA_MODES, export_scene, suggested_filename
from mandelbulb_viewer.presets import PRESETS, preset_settings
from mandelbulb_viewer.progressive import RenderPass


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("gallery"))
    parser.add_argument("--preset", choices=PRESETS, action="append")
    parser.add_argument("--fractal", choices=["mandelbulb", "julia"], default="mandelbulb")
    for axis, default in [("cx", 0.35), ("cy", 0.2), ("cz", 0.1)]:
        parser.add_argument(f"--{axis}", type=float, default=default)
    parser.add_argument("--width", type=int, default=1200)
    parser.add_argument("--height", type=int, default=1200)
    parser.add_argument("--samples", type=int, choices=[1, 2], default=1)
    parser.add_argument("--format", choices=["png", "gif", "mp4"], default="png")
    parser.add_argument(
        "--animation",
        choices=[
            "Camera Orbit",
            "Power Morph",
            "Palette Cycle",
            "Zoom",
            "Deep Zoom",
            "Spiral Dive",
            "Fractal Flythrough",
            *JULIA_MODES,
        ],
        default="Camera Orbit",
    )
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--seconds", type=int, default=6)
    parser.add_argument("--threads", type=int)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if not all(1 <= n <= 4096 // args.samples for n in (args.width, args.height)):
        parser.error("Invalid dimensions for selected supersampling")
    if not all(-1 <= v <= 1 for v in (args.cx, args.cy, args.cz)):
        parser.error("Julia constants must be within [-1, 1]")
    if not 1 <= args.fps <= 60 or not 1 <= args.seconds <= 120:
        parser.error("Invalid frame rate or duration")
    if args.format == "mp4" and (args.width % 2 or args.height % 2):
        parser.error("MP4 dimensions must be even")
    if (
        args.format == "gif"
        and args.fps * args.seconds * args.width * args.height * 3 > 256 * 1024**2
    ):
        parser.error("GIF too large; reduce dimensions or duration")
    if args.threads is not None:
        from numba import config, set_num_threads

        if not 1 <= args.threads <= config.NUMBA_NUM_THREADS:
            parser.error("Invalid thread count")
        if not args.dry_run:
            set_num_threads(args.threads)
    names = list(dict.fromkeys(args.preset or PRESETS))
    stage = RenderPass(args.width, args.height, args.samples)
    if not args.dry_run:
        args.output.mkdir(parents=True, exist_ok=True)
    for index, name in enumerate(names, 1):
        settings = preset_settings(name)
        if args.fractal == "julia" or (args.format != "png" and args.animation in JULIA_MODES):
            settings.update(fractal="Julia Bulb", cx=args.cx, cy=args.cy, cz=args.cz)
        mode = args.animation if args.format != "png" else "Camera Orbit"
        filename = suggested_filename(settings, stage, args.format, mode, args.fps, args.seconds)
        path = args.output / filename
        print(f"[{index}/{len(names)}] {name}: {path}", flush=True)
        if args.dry_run or (path.exists() and not args.overwrite):
            if not args.dry_run:
                print("  Skipped existing file", flush=True)
            continue
        start = time.monotonic()
        export_scene(
            path,
            Camera(),
            settings,
            stage,
            mode,
            args.fps,
            args.seconds,
            progress=lambda done, total: print(f"  Frame {done}/{total}", flush=True),
        )
        print(f"  Completed in {time.monotonic() - start:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
