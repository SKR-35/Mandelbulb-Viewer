"""Tk export dialog; worker communicates through a queue, never Tk calls."""

import tkinter as tk
from queue import Empty, Queue
from threading import Event
from time import monotonic
from tkinter import filedialog, messagebox, ttk

from mandelbulb_viewer.export import ExportCancelled, export_scene, suggested_filename
from mandelbulb_viewer.progressive import RenderPass


def open_export(viewer):
    dialog = tk.Toplevel(viewer.root)
    dialog.title("Export")
    dialog.transient(viewer.root)
    dialog.grab_set()
    fields = {}
    for name, default, options in (
        ("Format", "PNG", ("PNG", "GIF", "MP4")),
        ("Animation", "Camera Orbit", ("Camera Orbit", "Power Morph", "Palette Cycle", "Zoom")),
        ("Width", "640", None),
        ("Height", "480", None),
        ("FPS", "12", None),
        ("Seconds", "4", None),
        ("Samples per axis", "1", ("1", "2")),
    ):
        ttk.Label(dialog, text=name).pack(anchor="w", padx=12)
        var = tk.StringVar(value=default)
        fields[name] = var
        widget = (
            ttk.Entry(dialog, textvariable=var)
            if options is None
            else ttk.Combobox(dialog, textvariable=var, values=options, state="readonly")
        )
        widget.pack(fill="x", padx=12, pady=(0, 5))
    status = tk.StringVar(value="Ready")
    bar = ttk.Progressbar(dialog, maximum=100)
    bar.pack(fill="x", padx=12)
    ttk.Label(dialog, textvariable=status, wraplength=300).pack(padx=12, pady=5)
    cancel = Event()
    queue = Queue()
    future = None

    def close():
        if future is not None and not future.done():
            cancel.set()
            status.set("Cancelling after current frame…")
        else:
            dialog.destroy()

    def poll():
        try:
            while True:
                done, total = queue.get_nowait()
                bar.configure(value=100 * done / total)
                eta = (monotonic() - started[0]) / done * (total - done)
                status.set(f"{done}/{total} frames | ETA {eta:.0f}s")
        except Empty:
            pass
        if not future.done():
            dialog.after(100, poll)
            return
        try:
            future.result()
            status.set("Export complete")
        except ExportCancelled:
            status.set("Export cancelled")
        except Exception as exc:
            status.set(f"Export failed: {exc}")
        button.configure(state="normal")
        stop.configure(text="Close")

    started = [0.0]

    def start():
        nonlocal future
        try:
            w, h, samples, fps, seconds = (
                int(fields[k].get())
                for k in ("Width", "Height", "Samples per axis", "FPS", "Seconds")
            )
            if samples not in (1, 2) or not all(1 <= n <= 4096 // samples for n in (w, h)):
                raise ValueError("Invalid dimensions or sampling")
            if not 1 <= fps <= 60 or not 1 <= seconds <= 120:
                raise ValueError("Invalid FPS or duration")
        except ValueError as exc:
            messagebox.showerror("Export", str(exc), parent=dialog)
            return
        suffix = "." + fields["Format"].get().lower()
        settings = {k: v.get() for k, v in viewer.values.items() if k != "quality"}
        settings["iterations"] = int(round(settings["iterations"]))
        stage = RenderPass(w, h, samples)
        mode = fields["Animation"].get()
        path = filedialog.asksaveasfilename(
            parent=dialog,
            defaultextension=suffix,
            filetypes=[(suffix.upper(), "*" + suffix)],
            initialfile=suggested_filename(settings, stage, suffix, mode, fps, seconds),
        )
        if not path:
            return
        cancel.clear()
        bar.configure(value=0)
        started[0] = monotonic()
        button.configure(state="disabled")
        stop.configure(text="Cancel")
        status.set("Waiting for render worker…")
        future = viewer.submit_work(
            export_scene,
            path,
            viewer.camera,
            settings,
            RenderPass(w, h, samples),
            fields["Animation"].get(),
            fps,
            seconds,
            cancel.is_set,
            lambda d, t: queue.put((d, t)),
        )
        dialog.after(100, poll)

    button = ttk.Button(dialog, text="Export", command=start)
    button.pack(fill="x", padx=12)
    stop = ttk.Button(dialog, text="Close", command=close)
    stop.pack(fill="x", padx=12, pady=8)
    dialog.protocol("WM_DELETE_WINDOW", close)
