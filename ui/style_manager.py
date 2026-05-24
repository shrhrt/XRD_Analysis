from tkinter import ttk

_LIGHT = {
    "primary":      "#1565C0",
    "primary_fg":   "#FFFFFF",
    "primary_act":  "#0D47A1",
    "danger":       "#C62828",
    "danger_fg":    "#FFFFFF",
    "danger_act":   "#B71C1C",
    "label_fg":     "#1565C0",
    "select_bg":    "#1565C0",
    "select_fg":    "#FFFFFF",
}

_DARK = {
    "primary":      "#1E88E5",
    "primary_fg":   "#FFFFFF",
    "primary_act":  "#1565C0",
    "danger":       "#E53935",
    "danger_fg":    "#FFFFFF",
    "danger_act":   "#C62828",
    "label_fg":     "#90CAF9",
    "select_bg":    "#1E88E5",
    "select_fg":    "#FFFFFF",
}


def apply(mode: str = "light") -> None:
    p = _LIGHT if mode == "light" else _DARK
    s = ttk.Style()

    # Primary button (青・塗りつぶし)
    s.configure("Primary.TButton",
        background=p["primary"],
        foreground=p["primary_fg"],
        borderwidth=0, relief="flat",
        font=("", 9, "bold"),
        padding=[8, 5],
    )
    s.map("Primary.TButton",
        background=[("pressed", p["primary_act"]), ("active", p["primary_act"]), ("disabled", "#AAAAAA")],
        foreground=[("disabled", "#DDDDDD")],
        relief=[("pressed", "flat")],
    )

    # Danger button (赤・塗りつぶし)
    s.configure("Danger.TButton",
        background=p["danger"],
        foreground=p["danger_fg"],
        borderwidth=0, relief="flat",
        font=("", 9),
        padding=[8, 5],
    )
    s.map("Danger.TButton",
        background=[("pressed", p["danger_act"]), ("active", p["danger_act"]), ("disabled", "#AAAAAA")],
        foreground=[("disabled", "#DDDDDD")],
        relief=[("pressed", "flat")],
    )

    # LabelFrame タイトルを青・太字に
    s.configure("TLabelframe.Label",
        foreground=p["label_fg"],
        font=("", 9, "bold"),
    )

    # Notebook タブのパディングを広げて読みやすく
    s.configure("TNotebook.Tab",
        padding=[12, 5],
        font=("", 9),
    )


def listbox_colors(mode: str = "light") -> dict:
    p = _LIGHT if mode == "light" else _DARK
    return {"selectbackground": p["select_bg"], "selectforeground": p["select_fg"]}
