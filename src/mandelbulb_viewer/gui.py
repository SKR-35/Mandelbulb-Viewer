"""Desktop viewer with a single background render worker."""

import math
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from tkinter import ttk

import numpy as np
from PIL import Image, ImageTk

from mandelbulb_viewer.camera import Camera
from mandelbulb_viewer.lighting import render_image
from mandelbulb_viewer.palettes import DEFAULT_PALETTE, ORDER


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
        root.geometry("1100x760")
        self.camera = Camera()
        self.pool = ThreadPoolExecutor(max_workers=1)
        self.future = None
        self.pending = False
        self.closed = False
        self.timer = None
        self.photo = None
        self.last = (0, 0)
        panel = ttk.Frame(root, padding=12)
        panel.pack(side="left", fill="y")
        self.canvas = tk.Canvas(root, bg="#080a12", highlightthickness=0)
        self.canvas.pack(side="right", fill="both", expand=True)
        self.status = tk.StringVar(value="Ready")
        self.values = {}
        for name, default, options in (
            ("palette", DEFAULT_PALETTE, ORDER),
            ("color_mode", "angular", ("radial", "height", "angular")),
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

            def changed(value, label=label, name=name):
                label.configure(text=f"{name.replace('_', ' ').title()}: {float(value):.2f}")
                self.request()

            ttk.Scale(panel, from_=low, to=high, variable=var, command=changed).pack(fill="x")
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
        self.pending = True
        if self.timer is not None:
            self.root.after_cancel(self.timer)
        self.timer = self.root.after(180, self.start)

    def start(self):
        self.timer = None
        if self.closed or self.future is not None or not self.pending:
            return
        self.pending = False
        settings = {key: var.get() for key, var in self.values.items()}
        limit = {"Preview": 240, "Normal": 480, "High": 900}[settings.pop("quality")]
        settings["iterations"] = int(round(settings["iterations"]))
        w, h = max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())
        scale = min(1.0, limit / max(w, h))
        self.status.set("Rendering…")
        self.future = self.pool.submit(
            render_image, self.camera, max(1, int(w * scale)), max(1, int(h * scale)), **settings
        )
        self.root.after(60, self.poll)

    def poll(self):
        if self.closed:
            return
        if not self.future.done():
            self.root.after(60, self.poll)
            return
        try:
            image = self.future.result()
            if not self.pending:
                picture = Image.fromarray(image)
                picture.thumbnail((self.canvas.winfo_width(), self.canvas.winfo_height()))
                self.photo = ImageTk.PhotoImage(picture)
                self.canvas.delete("all")
                self.canvas.create_image(
                    self.canvas.winfo_width() // 2,
                    self.canvas.winfo_height() // 2,
                    image=self.photo,
                )
                self.status.set(f"Ready | {image.shape[1]} × {image.shape[0]}")
        except Exception as exc:
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
