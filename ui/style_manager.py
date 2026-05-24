import tkinter as tk
from tkinter import ttk

# Starbucks-inspired palette
_PRIMARY     = "#00704A"  # Starbucks green
_PRIMARY_FG  = "#FFFFFF"
_PRIMARY_ACT = "#005C3C"  # dark hover
_DANGER      = "#C62828"
_DANGER_FG   = "#FFFFFF"
_DANGER_ACT  = "#B71C1C"
_LABEL_LIGHT = "#1E3932"  # dark Starbucks green for LabelFrame titles
_LABEL_DARK  = "#80CBC4"  # teal for dark mode


def primary_btn(parent, text, command, **kwargs) -> tk.Button:
    """Green primary-action button (tk.Button for reliable color rendering on Windows)."""
    return tk.Button(
        parent, text=text, command=command,
        bg=_PRIMARY, fg=_PRIMARY_FG,
        activebackground=_PRIMARY_ACT, activeforeground=_PRIMARY_FG,
        relief="flat", borderwidth=0, cursor="hand2",
        font=("", 9, "bold"),
        **kwargs,
    )


def danger_btn(parent, text, command, **kwargs) -> tk.Button:
    """Red danger-action button (tk.Button for reliable color rendering on Windows)."""
    return tk.Button(
        parent, text=text, command=command,
        bg=_DANGER, fg=_DANGER_FG,
        activebackground=_DANGER_ACT, activeforeground=_DANGER_FG,
        relief="flat", borderwidth=0, cursor="hand2",
        font=("", 9),
        **kwargs,
    )


def apply(mode: str = "light") -> None:
    label_fg = _LABEL_LIGHT if mode == "light" else _LABEL_DARK
    s = ttk.Style()
    s.configure("TLabelframe.Label",
        foreground=label_fg,
        font=("", 9, "bold"),
    )
    s.configure("TNotebook.Tab",
        padding=[12, 5],
        font=("", 9),
    )


def listbox_colors(mode: str = "light") -> dict:
    return {"selectbackground": _PRIMARY, "selectforeground": _PRIMARY_FG}
