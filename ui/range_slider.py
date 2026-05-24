import tkinter as tk
from tkinter import ttk


class RangeSlider(tk.Canvas):
    """xmin/xmax を視覚的に設定するデュアルハンドルスライダー"""

    _TRACK_H = 4
    _HANDLE_R = 8
    _PAD = 20

    def __init__(self, parent, lo_var, hi_var, from_=0, to=180, **kwargs):
        kwargs.setdefault("height", 30)
        kwargs.setdefault("highlightthickness", 0)
        super().__init__(parent, **kwargs)
        self._from = from_
        self._to = to
        self._lo_var = lo_var
        self._hi_var = hi_var
        self._drag = None

        self.bind("<Configure>", lambda _: self._redraw())
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<B1-Motion>", self._motion)
        self.bind("<ButtonRelease-1>", lambda _: setattr(self, "_drag", None))

        lo_var.trace_add("write", lambda *_: self.after_idle(self._redraw))
        hi_var.trace_add("write", lambda *_: self.after_idle(self._redraw))

    def _track_w(self):
        return max(1, self.winfo_width() - 2 * self._PAD)

    def _to_x(self, val):
        ratio = (val - self._from) / (self._to - self._from)
        return self._PAD + ratio * self._track_w()

    def _to_val(self, x):
        ratio = (x - self._PAD) / self._track_w()
        return self._from + ratio * (self._to - self._from)

    def _get(self):
        try:
            lo = float(self._lo_var.get())
        except (ValueError, tk.TclError):
            lo = self._from
        try:
            hi = float(self._hi_var.get())
        except (ValueError, tk.TclError):
            hi = self._to
        return (
            max(self._from, min(self._to, lo)),
            max(self._from, min(self._to, hi)),
        )

    def _redraw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1:
            return

        bg = ttk.Style().lookup("TFrame", "background") or "#f0f0f0"
        fg = ttk.Style().lookup("TLabel", "foreground") or "#000000"
        self.configure(bg=bg)

        cy = h // 2
        lo, hi = self._get()
        xlo = self._to_x(lo)
        xhi = self._to_x(hi)
        r = self._HANDLE_R
        th = self._TRACK_H

        self.create_text(
            self._PAD - 2, cy, text=str(int(self._from)),
            anchor="e", font=("", 7), fill=fg,
        )
        self.create_text(
            w - self._PAD + 2, cy, text=str(int(self._to)),
            anchor="w", font=("", 7), fill=fg,
        )
        self.create_rectangle(
            self._PAD, cy - th // 2, w - self._PAD, cy + th // 2,
            fill="#aaaaaa", outline="",
        )
        self.create_rectangle(
            xlo, cy - th // 2, xhi, cy + th // 2,
            fill="#4a90d9", outline="",
        )
        for x in (xlo, xhi):
            self.create_oval(
                x - r, cy - r, x + r, cy + r,
                fill=bg, outline="#4a90d9", width=2,
            )

    def _press(self, event):
        lo, hi = self._get()
        xlo, xhi = self._to_x(lo), self._to_x(hi)
        r = self._HANDLE_R
        dlo = abs(event.x - xlo)
        dhi = abs(event.x - xhi)
        if dlo <= r or dhi <= r:
            self._drag = "lo" if dlo <= dhi else "hi"

    def _motion(self, event):
        if self._drag is None:
            return
        val = max(self._from, min(self._to, self._to_val(event.x)))
        lo, hi = self._get()
        if self._drag == "lo":
            self._lo_var.set(str(int(round(min(val, hi - 1)))))
        else:
            self._hi_var.set(str(int(round(max(val, lo + 1)))))
