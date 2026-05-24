import tkinter as tk
from tkinter import ttk


class AppearanceTab:
    """外観設定タブのUIを構築するクラス"""

    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.build()

    def _on_ann_text_change(self, event=None):
        content = self._ann_text.get("1.0", "end-1c")
        self._ann_updating = True
        self.app.model.annotation_text_var.set(content)
        self._ann_updating = False
        self.app.schedule_update()

    def _sync_ann_text_from_var(self, *_):
        if self._ann_updating:
            return
        value = self.app.model.annotation_text_var.get()
        current = self._ann_text.get("1.0", "end-1c")
        if value != current:
            self._ann_updating = True
            self._ann_text.delete("1.0", "end")
            self._ann_text.insert("1.0", value)
            self._ann_updating = False

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

        # --- テキストアノテーション ---
        ann_frame = ttk.LabelFrame(appearance_frame, text="テキストアノテーション")
        ann_frame.grid(row=15, column=0, columnspan=2, sticky="ew", pady=(10, 2))
        ann_frame.columnconfigure(1, weight=1)

        ttk.Checkbutton(
            ann_frame,
            text="表示する",
            variable=self.app.model.annotation_visible_var,
            command=self.app.schedule_update,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=2)

        ttk.Label(ann_frame, text="テキスト:").grid(row=1, column=0, sticky="nw", padx=5, pady=2)
        self._ann_text = tk.Text(ann_frame, height=3, width=22, wrap="none", relief="solid", borderwidth=1)
        self._ann_text.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        self._ann_text.insert("1.0", self.app.model.annotation_text_var.get())
        self._ann_updating = False
        self._ann_text.bind("<KeyRelease>", self._on_ann_text_change)
        self._ann_text.bind("<FocusOut>", self._on_ann_text_change)
        self.app.model.annotation_text_var.trace_add("write", self._sync_ann_text_from_var)

        ttk.Label(ann_frame, text="X位置:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        x_frame = ttk.Frame(ann_frame)
        x_frame.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        x_frame.columnconfigure(0, weight=1)
        x_val_lbl = ttk.Label(x_frame, text=f"{self.app.model.annotation_x_var.get():.2f}", width=4, anchor="e")
        x_val_lbl.grid(row=0, column=1, padx=(4, 0))
        ttk.Scale(
            x_frame,
            variable=self.app.model.annotation_x_var,
            from_=0.0, to=1.0, orient="horizontal",
            command=lambda v: (
                x_val_lbl.config(text=f"{float(v):.2f}"),
                self.app.schedule_update(),
            ),
        ).grid(row=0, column=0, sticky="ew")

        ttk.Label(ann_frame, text="Y位置:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        y_frame = ttk.Frame(ann_frame)
        y_frame.grid(row=3, column=1, sticky="ew", padx=5, pady=2)
        y_frame.columnconfigure(0, weight=1)
        y_val_lbl = ttk.Label(y_frame, text=f"{self.app.model.annotation_y_var.get():.2f}", width=4, anchor="e")
        y_val_lbl.grid(row=0, column=1, padx=(4, 0))
        ttk.Scale(
            y_frame,
            variable=self.app.model.annotation_y_var,
            from_=0.0, to=1.0, orient="horizontal",
            command=lambda v: (
                y_val_lbl.config(text=f"{float(v):.2f}"),
                self.app.schedule_update(),
            ),
        ).grid(row=0, column=0, sticky="ew")

        ttk.Label(ann_frame, text="フォントサイズ:").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        ttk.Spinbox(
            ann_frame,
            textvariable=self.app.model.annotation_fontsize_var,
            from_=6, to=60, increment=1,
            command=self.app.schedule_update,
        ).grid(row=4, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(
            ann_frame,
            text="※ Enterキーで改行。位置はグラフ領域内の比率 (右上=1,1 左下=0,0)",
            foreground="gray", font=("", 8), wraplength=290, justify="left",
        ).grid(row=5, column=0, columnspan=2, sticky="w", padx=5, pady=(0, 4))
