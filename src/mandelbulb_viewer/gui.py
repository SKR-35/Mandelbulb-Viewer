"""Desktop viewer with a single background render worker."""

import math
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from time import perf_counter
from tkinter import ttk

import numpy as np
from numba import config, set_num_threads
from PIL import Image, ImageTk

from mandelbulb_viewer.camera import Camera
from mandelbulb_viewer.export_dialog import open_export
from mandelbulb_viewer.palettes import DEFAULT_PALETTE, ORDER
from mandelbulb_viewer.presets import PRESETS, preset_settings
from mandelbulb_viewer.progressive import plan_passes, render_pass


def orbit(camera, dx, dy):
    offset = np.asarray(camera.position) - camera.target
    radius = np.linalg.norm(offset)
    azimuth = math.atan2(offset[1], offset[0]) - dx * 0.008
    elevation = math.asin(offset[2] / radius) + dy * 0.008
    elevation = max(-1.5, min(1.5, elevation))
    position = np.asarray(camera.target) + radius * np.array(
        [
            math.cos(elevation) * math.cos(azimuth),
            math.cos(elevation) * math.sin(azimuth),
            math.sin(elevation),
        ]
    )
    return replace(camera, position=tuple(position))


def pan(camera, dx, dy, height):
    origin, _, right, up = camera.frame()
    scale = 2 * np.linalg.norm(origin - camera.target) * math.tan(math.radians(camera.fov) / 2)
    shift = (-dx * right + dy * up) * scale / max(1, height)
    return replace(camera, position=tuple(origin + shift), target=tuple(camera.target + shift))


def zoom(camera, steps):
    # Change FOV rather than moving the camera inside the fractal.
    return replace(camera, fov=max(1.0, min(100.0, camera.fov * 0.85**steps)))


class Viewer:
    def __init__(self, root):
        self.root = root
        root.title("Mandelbulb Viewer")
        root.geometry("1100x800")
        self.camera = Camera()
        self.pool = ThreadPoolExecutor(max_workers=1)
        self.future = None
        self.pending = False
        self.generation = 0
        self.final_timer = None
        self.closed = False
        self.timer = None
        self.photo = None
        self.last = (0, 0)
        toolbar = ttk.Frame(root, padding=6)
        toolbar.pack(side="top", fill="x")
        ttk.Button(toolbar, text="Export…", command=lambda: open_export(self)).pack(side="right")
        ttk.Label(toolbar, text="CPU Threads:").pack(side="left")
        self.threads = tk.StringVar(value="Auto")
        ttk.Combobox(
            toolbar,
            textvariable=self.threads,
            state="readonly",
            width=7,
            values=("Auto", *map(str, range(1, config.NUMBA_NUM_THREADS + 1))),
        ).pack(side="left")
        julia_panel = ttk.LabelFrame(root, text="Julia Parameters", padding=6)
        julia_panel.pack(side="top", fill="x", padx=6, pady=(0, 4))
        panel = ttk.Frame(root, padding=12)
        panel.pack(side="left", fill="y")
        self.canvas = tk.Canvas(root, bg="#080a12", highlightthickness=0)
        self.canvas.pack(side="right", fill="both", expand=True)
        self.status = tk.StringVar(value="Ready")
        self.values = {}
        self.slider_labels = {}
        self.preset = tk.StringVar(value="Select preset")
        preset = ttk.Combobox(
            panel, textvariable=self.preset, values=tuple(PRESETS), state="readonly"
        )
        preset.pack(fill="x", pady=(0, 8))
        preset.bind("<<ComboboxSelected>>", self.apply_preset)
        for name, default, options in (
            ("fractal", "Mandelbulb", ("Mandelbulb", "Julia Bulb")),
            ("palette", DEFAULT_PALETTE, ORDER),
            ("color_mode", "angular", ("radial", "height", "angular", "orbit_trap")),
            ("quality", "Normal", ("Preview", "Normal", "High")),
        ):
            ttk.Label(panel, text=name.replace("_", " ").title()).pack(anchor="w")
            var = tk.StringVar(value=default)
            self.values[name] = var
            widget = ttk.Combobox(panel, textvariable=var, values=options, state="readonly")
            widget.pack(fill="x", pady=(0, 8))
            widget.bind("<<ComboboxSelected>>", self.request)
        for name, default, low, high in (
            ("power", 8.0, 2.0, 16.0),
            ("iterations", 20.0, 1.0, 80.0),
            ("color_cycles", 1.0, 0.1, 5.0),
            ("color_offset", 0.0, 0.0, 1.0),
            ("gamma", 1.0, 0.2, 3.0),
            ("ambient", 0.4, 0.0, 1.0),
            ("ao_strength", 0.65, 0.0, 1.0),
            ("exposure", 1.2, 0.1, 3.0),
        ):
            var = tk.DoubleVar(value=default)
            self.values[name] = var
            label = ttk.Label(panel, text=f"{name.replace('_', ' ').title()}: {default:.2f}")
            label.pack(anchor="w")
            self.slider_labels[name] = label

            def changed(value, label=label, name=name):
                label.configure(text=f"{name.replace('_', ' ').title()}: {float(value):.2f}")
                self.request()

            ttk.Scale(panel, from_=low, to=high, variable=var, command=changed).pack(fill="x")
        for column, (name, default) in enumerate((("cx", 0.35), ("cy", 0.2), ("cz", 0.1))):
            group = ttk.Frame(julia_panel)
            group.grid(row=0, column=column, sticky="ew", padx=6)
            julia_panel.columnconfigure(column, weight=1, uniform="julia")
            ttk.Label(group, text=name.capitalize()).pack(side="left", padx=(0, 4))
            var = tk.DoubleVar(value=default)
            self.values[name] = var
            display = tk.StringVar(value=f"{default:.3f}")
            entry = ttk.Entry(group, textvariable=display, width=8)
            entry.pack(side="right", padx=(4, 0))

            def commit(_event=None, var=var, display=display):
                try:
                    value = float(display.get().replace(",", "."))
                    if not math.isfinite(value) or not -1 <= value <= 1:
                        raise ValueError("Julia parameter outside range")
                except ValueError:
                    display.set(f"{var.get():.3f}")
                    return
                var.set(value)
                display.set(f"{value:.3f}")
                self.request()

            def sync(*_, var=var, display=display):
                display.set(f"{var.get():.3f}")

            var.trace_add("write", sync)
            entry.bind("<Return>", commit)
            entry.bind("<FocusOut>", commit)
            ttk.Scale(group, from_=-1, to=1, variable=var, command=self.request).pack(
                side="left", fill="x", expand=True
            )
        ttk.Button(panel, text="Render", command=self.request).pack(fill="x", pady=8)
        ttk.Button(panel, text="Reset camera", command=self.reset).pack(fill="x")
        ttk.Label(panel, textvariable=self.status, wraplength=210).pack(pady=8)
        for button in (1, 3):
            self.canvas.bind(f"<ButtonPress-{button}>", self.press)
            self.canvas.bind(f"<B{button}-Motion>", lambda e, b=button: self.drag(e, b))
        self.canvas.bind("<MouseWheel>", lambda e: self.wheel(e.delta / 120))
        self.canvas.bind("<Button-4>", lambda e: self.wheel(1))
        self.canvas.bind("<Button-5>", lambda e: self.wheel(-1))
        self.canvas.bind("<Configure>", self.request)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.request()

    def submit_work(self, function, *args):
        selection = self.threads.get()
        count = config.NUMBA_NUM_THREADS if selection == "Auto" else int(selection)

        def work():
            # Numba thread masks are local to the calling worker thread.
            set_num_threads(count)
            return function(*args)

        return self.pool.submit(work)

    def apply_preset(self, _event=None):
        for name, value in preset_settings(self.preset.get()).items():
            self.values[name].set(value)
            if name in self.slider_labels:
                self.slider_labels[name].configure(
                    text=f"{name.replace('_', ' ').title()}: {value:.2f}"
                )
        self.request()

    def press(self, event):
        self.last = event.x, event.y

    def drag(self, event, button):
        dx, dy = event.x - self.last[0], event.y - self.last[1]
        self.last = event.x, event.y
        if button == 1:
            self.camera = orbit(self.camera, dx, dy)
        else:
            self.camera = pan(self.camera, dx, dy, self.canvas.winfo_height())
        self.request()

    def wheel(self, steps):
        self.camera = zoom(self.camera, steps)
        self.request()

    def reset(self):
        self.camera = Camera()
        self.request()

    def request(self, *_):
        self.generation += 1
        self.pending = True
        if self.final_timer is not None:
            self.root.after_cancel(self.final_timer)
            self.final_timer = None
        if self.timer is not None:
            self.root.after_cancel(self.timer)
        self.timer = self.root.after(90, self.start)

    def start(self):
        self.timer = None
        if self.closed or self.future is not None or not self.pending:
            return
        self.pending = False
        settings = {key: var.get() for key, var in self.values.items()}
        quality = settings.pop("quality")
        settings["iterations"] = int(round(settings["iterations"]))
        w, h = max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())
        passes = plan_passes(w, h, quality)
        self.submit(self.generation, self.camera, settings, passes)

    def submit(self, generation, camera, settings, passes):
        self.final_timer = None
        if self.closed or generation != self.generation:
            return
        stage = passes[0]
        self.status.set("Rendering preview…" if len(passes) > 1 else "Rendering final…")
        self.started = perf_counter()
        self.future = self.submit_work(render_pass, camera, stage, settings)
        self.root.after(60, lambda: self.poll(generation, camera, settings, passes))

    def poll(self, generation, camera, settings, passes):
        if self.closed:
            return
        if not self.future.done():
            self.root.after(60, lambda: self.poll(generation, camera, settings, passes))
            return
        try:
            picture = self.future.result()
            if generation == self.generation:
                w, h = picture.size
                scale = min(self.canvas.winfo_width() / w, self.canvas.winfo_height() / h)
                picture = picture.resize(
                    (max(1, round(w * scale)), max(1, round(h * scale))), Image.Resampling.BILINEAR
                )
                self.photo = ImageTk.PhotoImage(picture)
                self.canvas.delete("all")
                self.canvas.create_image(
                    self.canvas.winfo_width() // 2,
                    self.canvas.winfo_height() // 2,
                    image=self.photo,
                )
                label = "Preview" if len(passes) > 1 else "Ready"
                self.status.set(f"{label} | {w} × {h} | {perf_counter() - self.started:.2f}s")
                if len(passes) > 1:
                    # Give input events a chance to invalidate expensive refinement.
                    self.final_timer = self.root.after(
                        350, lambda: self.submit(generation, camera, settings, passes[1:])
                    )
        except Exception as exc:
            if generation == self.generation:
                self.status.set(f"Render error: {exc}")
        finally:
            self.future = None
        if self.pending and self.timer is None:
            self.start()

    def close(self):
        self.closed = True
        self.pool.shutdown(wait=False, cancel_futures=True)
        self.root.destroy()


def main():
    root = tk.Tk()
    Viewer(root)
    root.mainloop()
