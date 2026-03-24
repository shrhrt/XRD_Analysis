import tkinter as tk
from tkinter import ttk


class AppearanceTab:
    """外観設定タブのUIを構築するクラス"""

    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.build()

    def build(self):
        appearance_frame = ttk.Frame(self.parent, padding=(10, 10))
        appearance_frame.pack(fill="x")
        appearance_frame.columnconfigure(1, weight=1)

        def create_row(
            parent, label_text, var, row, widget_class=ttk.Entry, **widget_args
        ):
            ttk.Label(parent, text=label_text).grid(
                row=row, column=0, sticky="w", pady=2
            )
            widget = widget_class(parent, textvariable=var, **widget_args)
            widget.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
            if isinstance(widget, (ttk.Spinbox, tk.Scale)):
                widget.configure(command=lambda *args: self.app.schedule_update())
            elif isinstance(widget, ttk.Entry):
                var.trace_add("write", self.app.schedule_update)

        create_row(appearance_frame, "X軸ラベル:", self.app.model.xlabel_var, 0)
        create_row(appearance_frame, "Y軸ラベル:", self.app.model.ylabel_var, 1)
        create_row(
            appearance_frame,
            "軸ラベルフォントサイズ:",
            self.app.model.axis_label_fontsize_var,
            2,
            ttk.Spinbox,
            from_=1,
            to=100,
        )
        create_row(
            appearance_frame,
            "目盛りフォントサイズ:",
            self.app.model.tick_label_fontsize_var,
            3,
            ttk.Spinbox,
            from_=1,
            to=100,
        )
        ttk.Label(appearance_frame, text="フォント:").grid(
            row=4, column=0, sticky="w", pady=2
        )
        font_combo = ttk.Combobox(
            appearance_frame,
            textvariable=self.app.model.font_family_var,
            values=[
                "sans-serif",
                "serif",
                "Arial",
                "Times New Roman",
                "Helvetica",
                "Courier New",
            ],
            state="readonly",
        )
        font_combo.grid(row=4, column=1, sticky="ew", padx=5, pady=2)
        font_combo.bind("<<ComboboxSelected>>", self.app.schedule_update)
        create_row(
            appearance_frame,
            "凡例フォントサイズ:",
            self.app.model.legend_fontsize_var,
            5,
            ttk.Spinbox,
            from_=1,
            to=100,
        )
        create_row(
            appearance_frame,
            "データ線の太さ:",
            self.app.model.plot_linewidth_var,
            6,
            ttk.Spinbox,
            from_=0.1,
            to=10,
            increment=0.1,
        )
        create_row(
            appearance_frame,
            "X軸主目盛り間隔:",
            self.app.model.xaxis_major_tick_spacing_var,
            7,
            ttk.Spinbox,
            from_=1,
            to=100,
        )
        ttk.Label(appearance_frame, text="X軸目盛りの向き:").grid(
            row=8, column=0, sticky="w", pady=2
        )
        dir_combo = ttk.Combobox(
            appearance_frame,
            textvariable=self.app.model.tick_direction_var,
            values=["in", "out", "inout"],
            state="readonly",
        )
        dir_combo.grid(row=8, column=1, sticky="ew", padx=5, pady=2)
        dir_combo.bind("<<ComboboxSelected>>", self.app.schedule_update)
        create_row(
            appearance_frame,
            "Y軸上部パディング係数:",
            self.app.model.ytop_padding_factor_var,
            9,
            ttk.Spinbox,
            from_=1,
            to=20,
            increment=0.1,
        )
        ttk.Checkbutton(
            appearance_frame,
            text="グリッドを表示",
            variable=self.app.model.show_grid_var,
            command=self.app.schedule_update,
        ).grid(row=10, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Checkbutton(
            appearance_frame,
            text="X軸主目盛りラベルを非表示",
            variable=self.app.model.hide_major_xtick_labels_var,
            command=self.app.schedule_update,
        ).grid(row=11, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Checkbutton(
            appearance_frame,
            text="X軸補助目盛りを表示",
            variable=self.app.model.show_minor_xticks_var,
            command=self.app._toggle_minor_xticks_widgets,
        ).grid(row=12, column=0, columnspan=2, sticky="w", pady=2)

        self.app.xminor_tick_spacing_label = ttk.Label(
            appearance_frame, text="X軸補助目盛り間隔:"
        )
        self.app.xminor_tick_spacing_label.grid(
            row=13, column=0, sticky="w", padx=5, pady=2
        )
        self.app.xminor_tick_spacing_entry = ttk.Spinbox(
            appearance_frame,
            textvariable=self.app.model.xminor_tick_spacing_var,
            from_=0.1,
            to=10,
            increment=0.1,
            command=self.app.schedule_update,
        )
        self.app.xminor_tick_spacing_entry.grid(
            row=13, column=1, sticky="ew", padx=5, pady=2
        )

        ttk.Checkbutton(
            appearance_frame,
            text="数式フォントを本文に合わせる",
            variable=self.app.model.match_math_font_var,
            command=self.app.schedule_update,
        ).grid(row=14, column=0, columnspan=2, sticky="w", pady=2)
