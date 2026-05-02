import tkinter as tk
from tkinter import ttk
from tkinter import colorchooser


class PlotSettingsTab:
    """プロット設定タブのUIを構築するクラス"""

    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.build()

    def build(self):
        tab = self.parent
        tab.columnconfigure(0, weight=1)

        file_frame = ttk.LabelFrame(tab, text="ファイル設定")
        file_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        file_frame.columnconfigure(0, weight=1)

        file_button_frame = ttk.Frame(file_frame)
        file_button_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        file_button_frame.columnconfigure(0, weight=1)
        file_button_frame.columnconfigure(1, weight=1)
        file_button_frame.columnconfigure(2, weight=1)

        ttk.Button(
            file_button_frame,
            text="ファイルを選択",
            command=self.app.file_handler.select_files,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 2))
        ttk.Button(
            file_button_frame,
            text="選択したファイルを削除",
            command=self.app.file_handler.remove_selected_file,
        ).grid(row=0, column=1, sticky="ew", padx=(2, 0))

        reorder_frame = ttk.Frame(file_button_frame)
        reorder_frame.grid(row=0, column=2, rowspan=2, padx=(5, 0))
        ttk.Button(
            reorder_frame, text="↑", command=self.app.file_handler.move_file_up
        ).pack(fill="x")
        ttk.Button(
            reorder_frame, text="↓", command=self.app.file_handler.move_file_down
        ).pack(fill="x")

        listbox_frame = ttk.Frame(file_frame)
        listbox_frame.grid(
            row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=(0, 5)
        )
        listbox_frame.rowconfigure(0, weight=1)
        listbox_frame.columnconfigure(0, weight=1)

        self.app.file_listbox = tk.Listbox(
            listbox_frame, selectmode=tk.SINGLE, height=6, exportselection=False
        )
        self.app.file_listbox.grid(row=0, column=0, sticky="nsew")
        self.app.file_listbox.bind(
            "<<ListboxSelect>>", self.app.file_handler.on_file_select
        )

        v_scrollbar = ttk.Scrollbar(
            listbox_frame, orient=tk.VERTICAL, command=self.app.file_listbox.yview
        )
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.app.file_listbox.config(yscrollcommand=v_scrollbar.set)
        h_scrollbar = ttk.Scrollbar(
            listbox_frame, orient=tk.HORIZONTAL, command=self.app.file_listbox.xview
        )
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        self.app.file_listbox.config(xscrollcommand=h_scrollbar.set)

        graph_settings_frame = ttk.LabelFrame(tab, text="グラフ設定")
        graph_settings_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        graph_settings_frame.columnconfigure(1, weight=1)

        ttk.Label(graph_settings_frame, text="横軸 最小値:").grid(
            row=0, column=0, sticky="w", padx=5, pady=2
        )
        self.app.xmin_entry = ttk.Entry(
            graph_settings_frame,
            textvariable=self.app.model.xmin_var,
            validate="all",
            validatecommand=self.app.vcmd_float,
        )
        self.app.xmin_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(graph_settings_frame, text="横軸 最大値:").grid(
            row=1, column=0, sticky="w", padx=5, pady=2
        )
        self.app.xmax_entry = ttk.Entry(
            graph_settings_frame,
            textvariable=self.app.model.xmax_var,
            validate="all",
            validatecommand=self.app.vcmd_float,
        )
        self.app.xmax_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(graph_settings_frame, text="強度しきい値:").grid(
            row=2, column=0, sticky="w", padx=5, pady=2
        )
        self.app.threshold_entry = ttk.Entry(
            graph_settings_frame,
            textvariable=self.app.model.threshold_var,
            validate="all",
            validatecommand=self.app.vcmd_float,
        )
        self.app.threshold_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

        threshold_handling_frame = ttk.Frame(graph_settings_frame)
        threshold_handling_frame.grid(row=3, column=0, columnspan=2, sticky="w", padx=5)
        ttk.Label(threshold_handling_frame, text="しきい値以下のデータ:").pack(
            side="left"
        )
        ttk.Radiobutton(
            threshold_handling_frame,
            text="非表示",
            variable=self.app.model.threshold_handling_var,
            value="hide",
            command=self.app.schedule_update,
        ).pack(side="left")
        ttk.Radiobutton(
            threshold_handling_frame,
            text="最小値に固定",
            variable=self.app.model.threshold_handling_var,
            value="clip",
            command=self.app.schedule_update,
        ).pack(side="left")

        yscale_frame = ttk.Frame(graph_settings_frame)
        yscale_frame.grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        ttk.Label(yscale_frame, text="Y軸スケール:").pack(side="left")
        ttk.Radiobutton(
            yscale_frame,
            text="Log",
            variable=self.app.model.yscale_var,
            value="log",
            command=self.app.schedule_update,
        ).pack(side="left")
        ttk.Radiobutton(
            yscale_frame,
            text="Linear",
            variable=self.app.model.yscale_var,
            value="linear",
            command=self.app.schedule_update,
        ).pack(side="left")

        ttk.Label(graph_settings_frame, text="凡例名 (数式は$で囲む):").grid(
            row=5, column=0, sticky="w", padx=5, pady=2
        )
        self.app.legend_name_entry = ttk.Entry(
            graph_settings_frame,
            textvariable=self.app.model.legend_name_var,
            state="disabled",
        )
        self.app.legend_name_entry.grid(row=5, column=1, sticky="ew", padx=5, pady=2)

        self.app.show_legend_check = ttk.Checkbutton(
            graph_settings_frame,
            text="凡例を表示する",
            variable=self.app.model.show_legend_var,
            command=self.app.schedule_update,
        )
        self.app.show_legend_check.grid(row=6, column=0, sticky="w", padx=5, pady=2)

        self.app.legend_loc_combo = ttk.Combobox(
            graph_settings_frame,
            textvariable=self.app.model.legend_loc_var,
            values=[
                "best",
                "upper right",
                "upper left",
                "lower left",
                "lower right",
                "right",
                "center left",
                "center right",
                "lower center",
                "upper center",
                "center",
            ],
            state="readonly",
        )
        self.app.legend_loc_combo.grid(row=6, column=1, sticky="ew", padx=5, pady=2)
        self.app.legend_loc_combo.bind("<<ComboboxSelected>>", self.app.schedule_update)

        legend_style_frame = ttk.Frame(graph_settings_frame)
        legend_style_frame.grid(
            row=7, column=0, columnspan=2, sticky="w", padx=5, pady=2
        )
        ttk.Checkbutton(
            legend_style_frame,
            text="枠線",
            variable=self.app.model.legend_frame_var,
            command=self.app.schedule_update,
        ).pack(side="left")
        ttk.Checkbutton(
            legend_style_frame,
            text="イタリック",
            variable=self.app.model.legend_italic_var,
            command=self.app.schedule_update,
        ).pack(side="left")
        ttk.Label(legend_style_frame, text="背景色:").pack(side="left", padx=(10, 2))

        self.app.legend_bg_button = tk.Button(
            legend_style_frame,
            text="■",
            width=2,
            relief=tk.SUNKEN,
            command=self._choose_legend_bgcolor,
        )
        self.app.legend_bg_button.pack(side="left")
        self.app.model.legend_bgcolor_var.trace_add(
            "write",
            lambda *args: self.app.legend_bg_button.config(
                fg=self.app.model.legend_bgcolor_var.get()
            ),
        )
        self.app.legend_bg_button.config(fg=self.app.model.legend_bgcolor_var.get())

        ttk.Checkbutton(
            graph_settings_frame,
            text="グラフを縦に並べる",
            variable=self.app.model.stack_plots_var,
            command=self.app._toggle_spacing_widget,
        ).grid(row=8, column=0, columnspan=2, sticky="w", padx=5, pady=2)

        self.app.spacing_label = ttk.Label(
            graph_settings_frame, text="グラフの間隔 (10^n)"
        )
        self.app.spacing_label.grid(row=9, column=0, sticky="w", padx=5, pady=2)

        self.app.spacing_entry = tk.Scale(
            graph_settings_frame,
            variable=self.app.model.plot_spacing_var,
            orient=tk.HORIZONTAL,
            from_=0,
            to=5,
            resolution=0.1,
            command=self.app.schedule_update,
        )
        self.app.spacing_entry.grid(row=9, column=1, sticky="ew", padx=5, pady=2)

        self.app.xmin_entry.bind("<FocusOut>", self.app.schedule_update)
        self.app.xmin_entry.bind("<Return>", self.app.schedule_update)
        self.app.xmax_entry.bind("<FocusOut>", self.app.schedule_update)
        self.app.xmax_entry.bind("<Return>", self.app.schedule_update)
        self.app.model.threshold_var.trace_add("write", self.app.schedule_update)
        self.app.model.legend_name_var.trace_add(
            "write", self.app.file_handler.on_legend_name_change
        )

    def _choose_legend_bgcolor(self):
        color = colorchooser.askcolor(
            title="凡例の背景色", initialcolor=self.app.model.legend_bgcolor_var.get()
        )
        if color and color[1]:
            self.app.model.legend_bgcolor_var.set(color[1])
            self.app.schedule_update()
