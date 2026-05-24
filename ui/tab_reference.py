import tkinter as tk
from tkinter import ttk
from tkinter import colorchooser


class ReferencePeaksTab:
    """参照ピークタブのUIとロジックを構築するクラス"""

    PREDEFINED_PEAKS_DB = {
        "γ-Fe2O3": [
            {"name": "(311)", "angle": "41.7"},
            {"name": "(440)", "angle": "74.8"},
            {"name": "(400)", "angle": "50.9"},
            {"name": "(111)", "angle": "21.4"},
            {"name": "(511)", "angle": "67.8"},
            {"name": "(220)", "angle": "35.4"},
            {"name": "(800)", "angle": "118.4"},
        ],
        "Fe3O4": [
            {"name": "(311)", "angle": "41.4"},
            {"name": "(440)", "angle": "74.1"},
            {"name": "(220)", "angle": "35.1"},
            {"name": "(400)", "angle": "50.4"},
            {"name": "(511)", "angle": "67.2"},
            {"name": "(111)", "angle": "21.3"},
            {"name": "(731)", "angle": "109.8"},
            {"name": "(422)", "angle": "62.9"},
            {"name": "(533)", "angle": "88.6"},
            {"name": "(800)", "angle": "116.9"},
        ],
        "MgO": [
            {"name": "(200)", "angle": "50.2"},
            {"name": "(220)", "angle": "73.7"},
            {"name": "(222)", "angle": "94.5"},
            {"name": "(111)", "angle": "43.1"},
            {"name": "(400)", "angle": "116.0"},
            {"name": "(311)", "angle": "89.3"},
        ],
        "Pt": [
            {"name": "(111)", "angle": "46.5"},
            {"name": "(200)", "angle": "54.2"},
            {"name": "(311)", "angle": "98.2"},
            {"name": "(220)", "angle": "80.3"},
            {"name": "(222)", "angle": "104.3"},
        ],
        "Cr": [
            {"name": "(110)", "angle": "52.0"},
            {"name": "(211)", "angle": "98.9"},
            {"name": "(220)", "angle": "122.6"},
            {"name": "(200)", "angle": "76.7"},
        ],
    }

    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.build()

    def build(self):
        tab = self.parent
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)

        top_container = tk.Frame(tab, padx=10, pady=10)
        top_container.grid(row=0, column=0, sticky="ew")
        top_container.columnconfigure(1, weight=1)

        preset_frame = tk.Frame(top_container)
        preset_frame.pack(fill="x", pady=(0, 5))
        tk.Label(preset_frame, text="プリセット読込:").pack(side="left")
        menubutton = tk.Menubutton(
            preset_frame, text="物質を選択...", relief=tk.RAISED, anchor="w"
        )
        menubutton.pack(side="left", fill="x", expand=True, padx=5)
        self._build_peak_preset_menu(menubutton)

        ttk.Button(
            preset_frame, text="SpinFilter", command=self.load_spin_filter_preset
        ).pack(side="left", padx=(10, 0))
        ttk.Button(preset_frame, text="クリア", command=self.clear_all_peaks).pack(
            side="left", padx=(10, 0)
        )

        peak_opts_frame = tk.Frame(top_container)
        peak_opts_frame.pack(fill="x")
        tk.Label(peak_opts_frame, text="フォントサイズ:").pack(side="left")
        ttk.Spinbox(
            peak_opts_frame,
            textvariable=self.app.model.peak_label_fontsize_var,
            from_=1,
            to=100,
            command=self.app.schedule_update,
            width=5,
        ).pack(side="left", padx=5)
        tk.Label(peak_opts_frame, text="Y位置(0-1):").pack(side="left", padx=(10, 0))
        ttk.Spinbox(
            peak_opts_frame,
            textvariable=self.app.model.peak_label_y_var,
            from_=0.0,
            to=1.0,
            increment=0.05,
            command=self.app.schedule_update,
            width=5,
        ).pack(side="left", padx=5)
        tk.Label(peak_opts_frame, text="ラベルオフセット:").pack(
            side="left", padx=(10, 0)
        )
        ttk.Spinbox(
            peak_opts_frame,
            textvariable=self.app.model.peak_label_offset_var,
            from_=0.1,
            to=5,
            increment=0.1,
            command=self.app.schedule_update,
            width=5,
        ).pack(side="left", padx=5)

        canvas_container = tk.LabelFrame(tab, text="ピークリスト")
        canvas_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        canvas_container.rowconfigure(0, weight=1)
        canvas_container.columnconfigure(0, weight=1)
        canvas = tk.Canvas(canvas_container, borderwidth=0, highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = tk.Scrollbar(
            canvas_container, orient="vertical", command=canvas.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)

        self.app.peak_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=self.app.peak_frame, anchor="nw")
        self.app.peak_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        self.app.peak_frame.columnconfigure(2, weight=1)
        self.app.peak_frame.columnconfigure(3, weight=1)

        tk.Label(self.app.peak_frame, text="表示").grid(row=0, column=1)
        tk.Label(self.app.peak_frame, text="物質名/結晶面").grid(row=0, column=2)
        tk.Label(self.app.peak_frame, text="2θ").grid(row=0, column=3)
        tk.Label(self.app.peak_frame, text="色").grid(row=0, column=4)
        tk.Label(self.app.peak_frame, text="線種").grid(row=0, column=5)

        linestyle_map = {"実線": "-", "破線": "--", "点線": ":", "一点鎖線": "-."}
        for i in range(10):
            tk.Label(self.app.peak_frame, text=f"#{i + 1}").grid(
                row=i + 1, column=0, padx=(5, 2), pady=2, sticky="w"
            )

            vis_var = tk.BooleanVar(value=False)
            tk.Checkbutton(
                self.app.peak_frame, variable=vis_var, command=self.app.schedule_update
            ).grid(row=i + 1, column=1)
            self.app.model.peak_visible_vars.append(vis_var)

            name_var = tk.StringVar()
            tk.Entry(self.app.peak_frame, textvariable=name_var).grid(
                row=i + 1, column=2, padx=2, pady=2, sticky="ew"
            )
            self.app.model.peak_name_vars.append(name_var)
            name_var.trace_add("write", self.app.schedule_update)

            angle_var = tk.StringVar()
            tk.Entry(self.app.peak_frame, textvariable=angle_var).grid(
                row=i + 1, column=3, padx=2, pady=2, sticky="ew"
            )
            self.app.model.peak_angle_vars.append(angle_var)
            angle_var.trace_add("write", self.app.schedule_update)

            color_var = tk.StringVar(value="#000000")
            color_button = tk.Button(
                self.app.peak_frame,
                text="■",
                width=2,
                relief=tk.SUNKEN,
                command=self._create_color_picker_command(i),
            )
            color_button.grid(row=i + 1, column=4, padx=2, pady=2)
            self.app.model.peak_color_vars.append(color_var)
            self.app.peak_color_buttons.append(color_button)

            style_var = tk.StringVar(value=linestyle_map["破線"])
            style_combo = ttk.Combobox(
                self.app.peak_frame,
                values=list(linestyle_map.keys()),
                width=6,
                state="readonly",
            )
            style_combo.set("破線")
            style_combo.bind(
                "<<ComboboxSelected>>",
                lambda e, v=style_var, c=style_combo, m=linestyle_map: (
                    v.set(m[c.get()]),
                    self.app.schedule_update(),
                ),
            )
            style_combo.grid(row=i + 1, column=5, padx=(2, 5), pady=2)
            self.app.model.peak_style_vars.append(style_var)

            tk.Button(
                self.app.peak_frame,
                text="×",
                command=lambda idx=i: self.clear_peak_row(idx),
                width=2,
            ).grid(row=i + 1, column=6, padx=(2, 5))

    def _build_peak_preset_menu(self, menubutton):
        menu = tk.Menu(menubutton, tearoff=0)
        menubutton.configure(menu=menu)
        for substance, peaks in self.PREDEFINED_PEAKS_DB.items():
            sub_menu = tk.Menu(menu, tearoff=0)
            menu.add_cascade(label=substance, menu=sub_menu)
            for i, peak in enumerate(peaks):
                sub_menu.add_command(
                    label=f"{peak['name']} ({peak['angle']})",
                    command=lambda p=peak, idx=i, s=substance: self.add_peak_to_list(
                        p, idx, s
                    ),
                )

    def add_peak_to_list(self, peak_data, target_index, substance):
        if 0 <= target_index < 10:
            self.app.model.peak_name_vars[target_index].set(
                f"{substance} {peak_data.get('name', '')}"
            )
            self.app.model.peak_angle_vars[target_index].set(peak_data.get("angle", ""))
            self.app.model.peak_visible_vars[target_index].set(True)
        self.app.schedule_update()

    def clear_peak_row(self, index):
        if 0 <= index < 10:
            self.app.model.peak_name_vars[index].set("")
            self.app.model.peak_angle_vars[index].set("")
            self.app.model.peak_visible_vars[index].set(False)
        self.app.schedule_update()

    def _create_color_picker_command(self, index):
        def command():
            color_code = colorchooser.askcolor(
                title="色を選択",
                initialcolor=self.app.model.peak_color_vars[index].get(),
            )
            if color_code and color_code[1]:
                self.app.model.peak_color_vars[index].set(color_code[1])
                self.app.peak_color_buttons[index].config(fg=color_code[1])
                self.app.schedule_update()

        return command

    def clear_all_peaks(self):
        for i in range(10):
            if i < len(self.app.model.peak_name_vars):
                self.app.model.peak_name_vars[i].set("")
                self.app.model.peak_angle_vars[i].set("")
                self.app.model.peak_visible_vars[i].set(False)
                self.app.model.peak_color_vars[i].set("#000000")
                self.app.peak_color_buttons[i].config(fg="#000000")
                self.app.model.peak_style_vars[i].set("--")
        self.app.schedule_update()

    def load_spin_filter_preset(self):
        spin_filter_data = [
            {
                "name": "Pt (111)",
                "angle": "46.5",
                "visible": True,
                "color": "#000000",
                "style": "--",
            },
            {
                "name": "Pt (200)",
                "angle": "54.2",
                "visible": True,
                "color": "#8000ff",
                "style": "--",
            },
            {
                "name": "γ-Fe2O3 (400)",
                "angle": "50.9",
                "visible": True,
                "color": "#0000ff",
                "style": "--",
            },
            {
                "name": "Fe3O4 (400)",
                "angle": "50.4",
                "visible": True,
                "color": "#000000",
                "style": "--",
            },
            {
                "name": "",
                "angle": "120.1",
                "visible": True,
                "color": "#000000",
                "style": "--",
            },
            {
                "name": "",
                "angle": "131.5",
                "visible": True,
                "color": "#000000",
                "style": "--",
            },
            {
                "name": "γ-Fe2O3 (004)",
                "angle": "50.876",
                "visible": False,
                "color": "#009300",
                "style": "--",
            },
            {
                "name": "Pt (111)",
                "angle": "46.50",
                "visible": True,
                "color": "#0000ff",
                "style": "--",
            },
            {
                "name": "Cr (002)",
                "angle": "76.5",
                "visible": True,
                "color": "#000000",
                "style": "--",
            },
            {
                "name": "",
                "angle": "",
                "visible": False,
                "color": "#000000",
                "style": "--",
            },
        ]

        for i, peak_data in enumerate(spin_filter_data):
            if i < len(self.app.model.peak_name_vars):
                self.app.model.peak_name_vars[i].set(peak_data.get("name", ""))
                self.app.model.peak_angle_vars[i].set(peak_data.get("angle", ""))
                self.app.model.peak_visible_vars[i].set(peak_data.get("visible", False))
                color = peak_data.get("color", "#000000")
                self.app.model.peak_color_vars[i].set(color)
                self.app.peak_color_buttons[i].config(fg=color)
                self.app.model.peak_style_vars[i].set(peak_data.get("style", "--"))

        self.app.schedule_update()
