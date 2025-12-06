import tkinter as tk
import os
from tkinter import ttk, filedialog, messagebox
import numpy as np
import math
from matplotlib.figure import Figure

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
import data_analyzer

class XRDPlotter(tk.Frame):
    PREDEFINED_PEAKS_DB = {
        "Fe3O4": [
            {'name': '(220)', 'angle': '30.1'}, {'name': '(311)', 'angle': '35.5'},
            {'name': '(400)', 'angle': '43.1'}, {'name': '(422)', 'angle': '53.4'},
            {'name': '(511)', 'angle': '57.0'}, {'name': '(440)', 'angle': '62.6'}
        ],
        "LiTi2O4": [
            {'name': '(111)', 'angle': '18.3'}, {'name': '(311)', 'angle': '35.5'},
            {'name': '(400)', 'angle': '43.1'}, {'name': '(331)', 'angle': '57.0'},
            {'name': '(440)', 'angle': '62.6'}
        ],
        "Li4Ti5O12": [
            {'name': '(111)', 'angle': '18.0'}, {'name': '(311)', 'angle': '35.4'},
            {'name': '(400)', 'angle': '43.1'}, {'name': '(511)', 'angle': '57.0'},
            {'name': '(440)', 'angle': '62.5'}
        ],
        "TiO2": [
            {'name': '(101)', 'angle': '25.3'}, {'name': '(004)', 'angle': '37.8'},
            {'name': '(200)', 'angle': '48.0'}, {'name': '(105)', 'angle': '53.9'},
            {'name': '(211)', 'angle': '55.1'}
        ]
    }

    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("XRD Data Plotter")
        self.master.geometry("1280x720")
        self.pack(fill=tk.BOTH, expand=True)

        self.peak_name_vars, self.peak_angle_vars, self.peak_visible_vars, self.peak_color_vars, self.peak_style_vars, self.peak_color_buttons = [], [], [], [], [], []
        self.xmin_var, self.xmax_var = tk.StringVar(value="30"), tk.StringVar(value="130")
        self.threshold_var, self.legend_name_var = tk.StringVar(value="1"), tk.StringVar()
        self.show_legend_var, self.stack_plots_var = tk.BooleanVar(value=True), tk.BooleanVar(value=False)
        self.threshold_handling_var = tk.StringVar(value="hide") # "hide" or "clip"
        self.plot_spacing_var = tk.DoubleVar(value=3)
        self.xlabel_var, self.ylabel_var = tk.StringVar(value="2θ/ω (degree)"), tk.StringVar(value="Log Intensity (arb. Units)")
        self.axis_label_fontsize_var, self.tick_label_fontsize_var = tk.DoubleVar(value=20), tk.DoubleVar(value=16)
        self.legend_fontsize_var, self.plot_linewidth_var = tk.DoubleVar(value=10), tk.DoubleVar(value=1.0)
        self.tick_direction_var = tk.StringVar(value='in')
        self.xaxis_major_tick_spacing_var, self.show_grid_var = tk.DoubleVar(value=10), tk.BooleanVar(value=False)
        self.ytop_padding_factor_var = tk.DoubleVar(value=1.5)
        self.hide_major_xtick_labels_var, self.show_minor_xticks_var = tk.BooleanVar(value=False), tk.BooleanVar(value=False)
        self.xminor_tick_spacing_var = tk.DoubleVar(value=1.0)
        self.peak_label_fontsize_var = tk.DoubleVar(value=9)
        self.peak_label_offset_var = tk.DoubleVar(value=0.4)
        self.d_spacing_input_2theta_var, self.d_spacing_result_var = tk.StringVar(), tk.StringVar(value="d-spacing (Å)")
        self.lc_input_d_var, self.lc_h_var, self.lc_k_var, self.lc_l_var = tk.StringVar(), tk.StringVar(value="1"), tk.StringVar(value="0"), tk.StringVar(value="0")
        self.lc_result_var = tk.StringVar(value="a = ?")
        self.export_width_var, self.export_height_var, self.export_format_var = tk.StringVar(value="6"), tk.StringVar(value="6"), tk.StringVar(value="png")
        self.selected_substance_var = tk.StringVar()
        
        # Analysis settings
        self.bg_subtract_enabled_var = tk.BooleanVar(value=False)
        self.bg_subtract_window_var = tk.IntVar(value=50)
        self.peak_detection_enabled_var = tk.BooleanVar(value=False)
        self.peak_detection_height_var = tk.DoubleVar(value=100)
        self.peak_detection_prominence_var = tk.DoubleVar(value=50)
        self.peak_detection_width_var = tk.DoubleVar(value=1)

        self._debounce_job, self.file_data, self.parsed_data = None, {}, {}
        
        self.fig = Figure(figsize=(6,4))
        self.ax = self.fig.add_subplot(111)

        self.create_widgets()

    def create_widgets(self):
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5)
        main_pane.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        left_panel = tk.Frame(main_pane, width=480); main_pane.add(left_panel, stretch="never")
        left_panel.rowconfigure(0, weight=1); left_panel.columnconfigure(0, weight=1)

        notebook = ttk.Notebook(left_panel); notebook.grid(row=0, column=0, sticky="nsew")
        plot_settings_tab, appearance_tab, analysis_tab, export_tab = tk.Frame(notebook), tk.Frame(notebook), tk.Frame(notebook), tk.Frame(notebook)
        notebook.add(plot_settings_tab, text="プロット設定"); notebook.add(appearance_tab, text="外観設定"); notebook.add(analysis_tab, text="解析ツール"); notebook.add(export_tab, text="エクスポート")
        
        self.build_plot_settings_tab(plot_settings_tab)
        self.build_appearance_tab(appearance_tab)
        self.build_analysis_tab(analysis_tab)
        self.build_export_tab(export_tab)

        plot_panel = tk.Frame(main_pane); main_pane.add(plot_panel, stretch="always")
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_panel); self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(self.canvas, plot_panel); toolbar.update()
        
        self._toggle_spacing_widget(); self._toggle_minor_xticks_widgets(); self.update_plot()

    def build_plot_settings_tab(self, tab):
        tab.rowconfigure(2, weight=1); tab.columnconfigure(0, weight=1)
        file_frame = tk.LabelFrame(tab, text="ファイル設定"); file_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10)); file_frame.columnconfigure(0, weight=1)
        file_button_frame = tk.Frame(file_frame); file_button_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5); file_button_frame.columnconfigure(0, weight=1); file_button_frame.columnconfigure(1, weight=1); file_button_frame.columnconfigure(2, weight=1)
        tk.Button(file_button_frame, text="ファイルを選択", command=self.select_files).grid(row=0, column=0, sticky="ew", padx=(0, 2))
        tk.Button(file_button_frame, text="選択したファイルを削除", command=self.remove_selected_file).grid(row=0, column=1, sticky="ew", padx=(2, 0))
        reorder_frame = tk.Frame(file_button_frame); reorder_frame.grid(row=0, column=2, rowspan=2, padx=(5,0)); tk.Button(reorder_frame, text="↑", command=self.move_file_up).pack(fill='x'); tk.Button(reorder_frame, text="↓", command=self.move_file_down).pack(fill='x')
        listbox_frame = tk.Frame(file_frame); listbox_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=(0, 5)); listbox_frame.rowconfigure(0, weight=1); listbox_frame.columnconfigure(0, weight=1)
        self.file_listbox = tk.Listbox(listbox_frame, selectmode=tk.SINGLE, height=6, exportselection=False); self.file_listbox.grid(row=0, column=0, sticky="nsew"); self.file_listbox.bind("<<ListboxSelect>>", self.on_file_select)
        v_scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.file_listbox.yview); v_scrollbar.grid(row=0, column=1, sticky="ns"); self.file_listbox.config(yscrollcommand=v_scrollbar.set)
        h_scrollbar = tk.Scrollbar(listbox_frame, orient=tk.HORIZONTAL, command=self.file_listbox.xview); h_scrollbar.grid(row=1, column=0, sticky="ew"); self.file_listbox.config(xscrollcommand=h_scrollbar.set)
        
        graph_settings_frame = tk.LabelFrame(tab, text="グラフ設定"); graph_settings_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10)); graph_settings_frame.columnconfigure(1, weight=1)
        tk.Label(graph_settings_frame, text="横軸 最小値:").grid(row=0, column=0, sticky="w", padx=5, pady=2); self.xmin_entry = tk.Entry(graph_settings_frame, textvariable=self.xmin_var); self.xmin_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        tk.Label(graph_settings_frame, text="横軸 最大値:").grid(row=1, column=0, sticky="w", padx=5, pady=2); self.xmax_entry = tk.Entry(graph_settings_frame, textvariable=self.xmax_var); self.xmax_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        tk.Label(graph_settings_frame, text="強度しきい値:").grid(row=2, column=0, sticky="w", padx=5, pady=2); self.threshold_entry = tk.Entry(graph_settings_frame, textvariable=self.threshold_var); self.threshold_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        threshold_handling_frame = tk.Frame(graph_settings_frame); threshold_handling_frame.grid(row=3, column=0, columnspan=2, sticky="w", padx=5)
        tk.Label(threshold_handling_frame, text="しきい値以下のデータ:").pack(side="left")
        tk.Radiobutton(threshold_handling_frame, text="非表示", variable=self.threshold_handling_var, value="hide", command=self.schedule_update).pack(side="left")
        tk.Radiobutton(threshold_handling_frame, text="最小値に固定", variable=self.threshold_handling_var, value="clip", command=self.schedule_update).pack(side="left")
        tk.Label(graph_settings_frame, text="凡例名:").grid(row=4, column=0, sticky="w", padx=5, pady=2); self.legend_name_entry = tk.Entry(graph_settings_frame, textvariable=self.legend_name_var, state="disabled"); self.legend_name_entry.grid(row=4, column=1, sticky="ew", padx=5, pady=2)
        self.show_legend_check = tk.Checkbutton(graph_settings_frame, text="凡例を表示する", variable=self.show_legend_var, command=self.toggle_legend_visibility); self.show_legend_check.grid(row=5, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        tk.Checkbutton(graph_settings_frame, text="グラフを縦に並べる", variable=self.stack_plots_var, command=self._toggle_spacing_widget).grid(row=6, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        self.spacing_label = tk.Label(graph_settings_frame, text="グラフの間隔 (10^n)"); self.spacing_label.grid(row=7, column=0, sticky="w", padx=5, pady=2)
        self.spacing_entry = tk.Scale(graph_settings_frame, variable=self.plot_spacing_var, orient=tk.HORIZONTAL, from_=0, to=5, resolution=0.1, command=self.schedule_update); self.spacing_entry.grid(row=7, column=1, sticky="ew", padx=5, pady=2)
        self.xmin_entry.bind("<FocusOut>", self.schedule_update); self.xmin_entry.bind("<Return>", self.schedule_update); self.xmax_entry.bind("<FocusOut>", self.schedule_update); self.xmax_entry.bind("<Return>", self.schedule_update); self.threshold_var.trace_add("write", self.schedule_update); self.legend_name_var.trace_add("write", self.on_legend_name_change)
        
        container = tk.LabelFrame(tab, text="参照ピーク設定"); container.grid(row=2, column=0, sticky="nsew"); container.rowconfigure(2, weight=1); container.columnconfigure(0, weight=1)
        preset_frame = tk.Frame(container); preset_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5,0)); preset_frame.columnconfigure(1, weight=1)
        tk.Label(preset_frame, text="プリセット読込:").grid(row=0, column=0, sticky="w")
        menubutton = tk.Menubutton(preset_frame, text="物質を選択...", relief=tk.RAISED, anchor="w")
        menubutton.grid(row=0, column=1, sticky="ew")
        self._build_peak_preset_menu(menubutton)
        
        peak_opts_frame = tk.Frame(container)
        peak_opts_frame.grid(row=1, column=0, sticky="ew", padx=5)
        peak_opts_frame.columnconfigure(1, weight=1)
        peak_opts_frame.columnconfigure(3, weight=1)
        tk.Label(peak_opts_frame, text="フォントサイズ:").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(peak_opts_frame, textvariable=self.peak_label_fontsize_var, from_=1, to=100, command=self.schedule_update, width=5).grid(row=0, column=1, sticky="w")
        tk.Label(peak_opts_frame, text="ラベルオフセット:").grid(row=0, column=2, sticky="w", padx=(10,0))
        ttk.Spinbox(peak_opts_frame, textvariable=self.peak_label_offset_var, from_=0.1, to=5, increment=0.1, command=self.schedule_update, width=5).grid(row=0, column=3, sticky="w")

        canvas_container = tk.Frame(container); canvas_container.grid(row=2, column=0, sticky="nsew"); canvas_container.rowconfigure(0, weight=1); canvas_container.columnconfigure(0, weight=1)
        canvas = tk.Canvas(canvas_container, borderwidth=0, highlightthickness=0); canvas.grid(row=0, column=0, sticky="nsew"); scrollbar = tk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview); scrollbar.grid(row=0, column=1, sticky="ns"); canvas.configure(yscrollcommand=scrollbar.set); self.peak_frame = tk.Frame(canvas); canvas.create_window((0, 0), window=self.peak_frame, anchor="nw"); self.peak_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))); self.peak_frame.columnconfigure(2, weight=1); self.peak_frame.columnconfigure(3, weight=1)
        tk.Label(self.peak_frame, text="表示").grid(row=0, column=1); tk.Label(self.peak_frame, text="物質名/結晶面").grid(row=0, column=2); tk.Label(self.peak_frame, text="2θ").grid(row=0, column=3); tk.Label(self.peak_frame, text="色").grid(row=0, column=4); tk.Label(self.peak_frame, text="線種").grid(row=0, column=5)
        linestyle_map = {"実線": "-", "破線": "--", "点線": ":", "一点鎖線": "-. "}
        for i in range(10):
            tk.Label(self.peak_frame, text=f"#{i+1}").grid(row=i+1, column=0, padx=(5,2), pady=2, sticky="w"); vis_var = tk.BooleanVar(value=False); tk.Checkbutton(self.peak_frame, variable=vis_var, command=self.schedule_update).grid(row=i+1, column=1); self.peak_visible_vars.append(vis_var); name_var = tk.StringVar(); tk.Entry(self.peak_frame, textvariable=name_var).grid(row=i+1, column=2, padx=2, pady=2, sticky="ew"); self.peak_name_vars.append(name_var); name_var.trace_add("write", self.schedule_update); angle_var = tk.StringVar(); tk.Entry(self.peak_frame, textvariable=angle_var).grid(row=i+1, column=3, padx=2, pady=2, sticky="ew"); self.peak_angle_vars.append(angle_var); angle_var.trace_add("write", self.schedule_update); color_var = tk.StringVar(value="#000000"); color_button = tk.Button(self.peak_frame, text="■", width=2, relief=tk.SUNKEN, command=self._create_color_picker_command(i)); color_button.grid(row=i+1, column=4, padx=2, pady=2); self.peak_color_vars.append(color_var); self.peak_color_buttons.append(color_button); style_var = tk.StringVar(value=linestyle_map["破線"]); style_combo = ttk.Combobox(self.peak_frame, values=list(linestyle_map.keys()), width=6, state="readonly"); style_combo.set("破線"); style_combo.bind("<<ComboboxSelected>>", lambda e, v=style_var, c=style_combo, m=linestyle_map: (v.set(m[c.get()]), self.schedule_update())); style_combo.grid(row=i+1, column=5, padx=(2,5), pady=2); self.peak_style_vars.append(style_var)
            tk.Button(self.peak_frame, text="×", command=lambda i=i: self.clear_peak_row(i), width=2).grid(row=i+1, column=6, padx=(2,5))
    
    def build_appearance_tab(self, tab):
        appearance_frame = tk.Frame(tab, padx=10, pady=10); appearance_frame.pack(fill="x"); appearance_frame.columnconfigure(1, weight=1)
        def create_row(parent, label_text, var, row, widget_class=tk.Entry, **widget_args):
            tk.Label(parent, text=label_text).grid(row=row, column=0, sticky="w", pady=2); widget = widget_class(parent, textvariable=var, **widget_args); widget.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
            if isinstance(widget, (ttk.Spinbox, tk.Scale)): widget.configure(command=lambda *args: self.schedule_update())
            elif isinstance(widget, tk.Entry): var.trace_add("write", self.schedule_update)
        create_row(appearance_frame, "X軸ラベル:", self.xlabel_var, 0); create_row(appearance_frame, "Y軸ラベル:", self.ylabel_var, 1)
        create_row(appearance_frame, "軸ラベルフォントサイズ:", self.axis_label_fontsize_var, 2, ttk.Spinbox, from_=1, to=100); create_row(appearance_frame, "目盛りフォントサイズ:", self.tick_label_fontsize_var, 3, ttk.Spinbox, from_=1, to=100)
        create_row(appearance_frame, "凡例フォントサイズ:", self.legend_fontsize_var, 4, ttk.Spinbox, from_=1, to=100); 
        create_row(appearance_frame, "データ線の太さ:", self.plot_linewidth_var, 5, ttk.Spinbox, from_=0.1, to=10, increment=0.1)
        create_row(appearance_frame, "X軸主目盛り間隔:", self.xaxis_major_tick_spacing_var, 6, ttk.Spinbox, from_=1, to=100)
        tk.Label(appearance_frame, text="X軸目盛りの向き:").grid(row=7, column=0, sticky="w", pady=2)
        dir_combo = ttk.Combobox(appearance_frame, textvariable=self.tick_direction_var, values=['in', 'out', 'inout'], state="readonly"); dir_combo.grid(row=7, column=1, sticky="ew", padx=5, pady=2); dir_combo.bind("<<ComboboxSelected>>", self.schedule_update)
        create_row(appearance_frame, "Y軸上部パディング係数:", self.ytop_padding_factor_var, 8, ttk.Spinbox, from_=1, to=20, increment=0.1)
        tk.Checkbutton(appearance_frame, text="グリッドを表示", variable=self.show_grid_var, command=self.schedule_update).grid(row=9, column=0, columnspan=2, sticky="w", pady=2)
        tk.Checkbutton(appearance_frame, text="X軸主目盛りラベルを非表示", variable=self.hide_major_xtick_labels_var, command=self.schedule_update).grid(row=10, column=0, columnspan=2, sticky="w", pady=2)
        tk.Checkbutton(appearance_frame, text="X軸補助目盛りを表示", variable=self.show_minor_xticks_var, command=self._toggle_minor_xticks_widgets).grid(row=11, column=0, columnspan=2, sticky="w", pady=2)
        self.xminor_tick_spacing_label = tk.Label(appearance_frame, text="X軸補助目盛り間隔:"); self.xminor_tick_spacing_label.grid(row=12, column=0, sticky="w", padx=5, pady=2)
        self.xminor_tick_spacing_entry = ttk.Spinbox(appearance_frame, textvariable=self.xminor_tick_spacing_var, from_=0.1, to=10, increment=0.1, command=self.schedule_update); self.xminor_tick_spacing_entry.grid(row=12, column=1, sticky="ew", padx=5, pady=2)

    def build_analysis_tab(self, tab):
        analysis_frame = tk.Frame(tab, padx=10, pady=10); analysis_frame.pack(fill="x", anchor="n")
        analysis_frame.columnconfigure(0, weight=1)

        # d-spacing tool
        d_spacing_frame = tk.LabelFrame(analysis_frame, text="d値計算ツール"); d_spacing_frame.grid(row=0, column=0, sticky="ew", pady=5); d_spacing_frame.columnconfigure(1, weight=1)
        tk.Label(d_spacing_frame, text="ブラッグの式: nλ = 2d sin(θ)").grid(row=0, column=0, columnspan=3, sticky="w", padx=5)
        tk.Label(d_spacing_frame, text="定数: X線=Co Kα1 (λ=1.78897 Å), n=1").grid(row=1, column=0, columnspan=3, sticky="w", padx=5)
        tk.Label(d_spacing_frame, text="2θ (degree):").grid(row=2, column=0, sticky="w", padx=5, pady=5); d_input_entry = tk.Entry(d_spacing_frame, textvariable=self.d_spacing_input_2theta_var); d_input_entry.grid(row=2, column=1, sticky="ew", padx=5); tk.Button(d_spacing_frame, text="計算", command=self.calculate_d_spacing).grid(row=2, column=2, padx=5)
        tk.Label(d_spacing_frame, textvariable=self.d_spacing_result_var, relief="sunken").grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5); d_input_entry.bind("<Return>", self.calculate_d_spacing)
        
        # Lattice constant tool
        lc_frame = tk.LabelFrame(analysis_frame, text="格子定数計算ツール (立方晶のみ)"); lc_frame.grid(row=1, column=0, sticky="ew", pady=5); lc_frame.columnconfigure(1, weight=1)
        tk.Label(lc_frame, text="式: a = d * √(h² + k² + l²)").grid(row=0, column=0, columnspan=3, sticky="w", padx=5)
        tk.Label(lc_frame, text="d-spacing (Å):").grid(row=1, column=0, sticky="w", padx=5, pady=5); lc_d_entry = tk.Entry(lc_frame, textvariable=self.lc_input_d_var); lc_d_entry.grid(row=1, column=1, sticky="ew", padx=5); tk.Button(lc_frame, text="コピー", command=self.copy_d_spacing).grid(row=1, column=2, padx=5)
        hkl_frame = tk.Frame(lc_frame); hkl_frame.grid(row=2, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        tk.Label(hkl_frame, text="面指数 (h, k, l):").pack(side="left"); tk.Entry(hkl_frame, textvariable=self.lc_h_var, width=5).pack(side="left"); tk.Entry(hkl_frame, textvariable=self.lc_k_var, width=5).pack(side="left"); tk.Entry(hkl_frame, textvariable=self.lc_l_var, width=5).pack(side="left")
        tk.Button(lc_frame, text="計算", command=self.calculate_lattice_constant).grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        tk.Label(lc_frame, textvariable=self.lc_result_var, relief="sunken").grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        # Background subtraction
        bg_frame = tk.LabelFrame(analysis_frame, text="バックグラウンド除去"); bg_frame.grid(row=2, column=0, sticky="ew", pady=5); bg_frame.columnconfigure(1, weight=1)
        tk.Checkbutton(bg_frame, text="有効化", variable=self.bg_subtract_enabled_var, command=self.schedule_update).grid(row=0, column=0, sticky="w", padx=5)
        tk.Label(bg_frame, text="ウィンドウサイズ:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Spinbox(bg_frame, textvariable=self.bg_subtract_window_var, from_=1, to=1000, command=self.schedule_update, width=10).grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        # Peak detection
        peak_frame = tk.LabelFrame(analysis_frame, text="ピーク検出"); peak_frame.grid(row=3, column=0, sticky="ew", pady=5); peak_frame.columnconfigure(1, weight=1)
        tk.Checkbutton(peak_frame, text="有効化", variable=self.peak_detection_enabled_var, command=self.schedule_update).grid(row=0, column=0, columnspan=2, sticky="w", padx=5)
        tk.Label(peak_frame, text="最小高さ:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Spinbox(peak_frame, textvariable=self.peak_detection_height_var, from_=0, to=1e9, increment=10, command=self.schedule_update).grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        tk.Label(peak_frame, text="最小プロミネンス:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ttk.Spinbox(peak_frame, textvariable=self.peak_detection_prominence_var, from_=0, to=1e9, increment=10, command=self.schedule_update).grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        tk.Label(peak_frame, text="最小幅:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        ttk.Spinbox(peak_frame, textvariable=self.peak_detection_width_var, from_=0, to=100, increment=0.5, command=self.schedule_update).grid(row=3, column=1, sticky="ew", padx=5, pady=2)

    def build_export_tab(self, tab):
        export_frame = tk.LabelFrame(tab, text="画像ファイルとして保存"); export_frame.pack(fill="x", padx=10, pady=10); export_frame.columnconfigure(1, weight=1)
        tk.Label(export_frame, text="幅 (inch):").grid(row=0, column=0, sticky="w", padx=5, pady=2); tk.Entry(export_frame, textvariable=self.export_width_var).grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        tk.Label(export_frame, text="高さ (inch):").grid(row=1, column=0, sticky="w", padx=5, pady=2); tk.Entry(export_frame, textvariable=self.export_height_var).grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        tk.Label(export_frame, text="形式:").grid(row=2, column=0, sticky="w", padx=5, pady=2); ttk.Combobox(export_frame, textvariable=self.export_format_var, values=["png", "pdf", "svg"], state="readonly").grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        
        button_frame = tk.Frame(export_frame)
        button_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=(10, 5))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        tk.Button(button_frame, text="プレビュー", command=self.preview_figure).grid(row=0, column=0, sticky="ew", padx=(0,2))
        tk.Button(button_frame, text="グラフを保存", command=self.save_figure, font=("", 10, "bold")).grid(row=0, column=1, sticky="ew", padx=(2,0))


    def _toggle_spacing_widget(self, *args):
        if self.stack_plots_var.get(): self.spacing_label.grid(); self.spacing_entry.grid()
        else: self.spacing_label.grid_remove(); self.spacing_entry.grid_remove()
        self.schedule_update()

    def _toggle_minor_xticks_widgets(self, *args):
        if self.show_minor_xticks_var.get(): self.xminor_tick_spacing_label.grid(); self.xminor_tick_spacing_entry.grid()
        else: self.xminor_tick_spacing_label.grid_remove(); self.xminor_tick_spacing_entry.grid_remove()
        self.schedule_update()

    def _build_peak_preset_menu(self, menubutton):
        menu = tk.Menu(menubutton, tearoff=0)
        menubutton.configure(menu=menu)
        for substance, peaks in self.PREDEFINED_PEAKS_DB.items():
            sub_menu = tk.Menu(menu, tearoff=0)
            menu.add_cascade(label=substance, menu=sub_menu)
            for i, peak in enumerate(peaks):
                sub_menu.add_command(label=f"{peak['name']} ({peak['angle']})", command=lambda p=peak, idx=i, s=substance: self.add_peak_to_list(p, idx, s))

    def add_peak_to_list(self, peak_data, target_index, substance):
        if 0 <= target_index < 10:
            full_name = f"{substance} {peak_data.get('name', '')}"
            self.peak_name_vars[target_index].set(full_name)
            self.peak_angle_vars[target_index].set(peak_data.get('angle', ''))
            self.peak_visible_vars[target_index].set(True)
        self.schedule_update()

    def clear_peak_row(self, index):
        if 0 <= index < 10:
            self.peak_name_vars[index].set("")
            self.peak_angle_vars[index].set("")
            self.peak_visible_vars[index].set(False)
        self.schedule_update()

    def _create_color_picker_command(self, index):
        from tkinter import colorchooser
        def command():
            color_code = colorchooser.askcolor(title="色を選択", initialcolor=self.peak_color_vars[index].get())
            if color_code and color_code[1]: self.peak_color_vars[index].set(color_code[1]); self.peak_color_buttons[index].config(fg=color_code[1]); self.schedule_update()
        return command
    
    def _get_current_plot_settings(self):
        filepaths = self.file_listbox.get(0, tk.END)
        plot_data_full = [{'label': self.file_data[fp], 'angles': self.parsed_data[fp][0], 'intensities': self.parsed_data[fp][1]} for fp in filepaths if fp in self.file_data and fp in self.parsed_data]
        
        try:
            threshold = float(self.threshold_var.get()) if self.threshold_var.get() else 0.0
            spacing = self.plot_spacing_var.get()
            xmin = float(self.xmin_var.get()) if self.xmin_var.get() else None
            xmax = float(self.xmax_var.get()) if self.xmax_var.get() else None
            if xmin is not None and xmax is not None and xmin >= xmax:
                messagebox.showwarning("警告", "横軸の最小値は最大値より小さくしてください。")
                return None
        except ValueError:
            messagebox.showwarning("警告", "グラフ設定の数値が不正です。")
            return None
            
        reference_peaks = [{'name': self.peak_name_vars[i].get().strip(), 'angle': float(self.peak_angle_vars[i].get().strip()), 'visible': self.peak_visible_vars[i].get(), 'color': self.peak_color_vars[i].get(), 'linestyle': self.peak_style_vars[i].get()} for i in range(10) if self.peak_name_vars[i].get().strip() and self.peak_angle_vars[i].get().strip()]
        
        appearance_settings = {
            'xlabel': self.xlabel_var.get(), 'ylabel': self.ylabel_var.get(), 'axis_label_fontsize': self.axis_label_fontsize_var.get(), 'tick_label_fontsize': self.tick_label_fontsize_var.get(),
            'legend_fontsize': self.legend_fontsize_var.get(), 'linewidth': self.plot_linewidth_var.get(), 'tick_direction': self.tick_direction_var.get(), 'threshold_handling': self.threshold_handling_var.get(),
            'xaxis_major_tick_spacing': self.xaxis_major_tick_spacing_var.get(), 'show_grid': self.show_grid_var.get(), 'ytop_padding_factor': self.ytop_padding_factor_var.get(),
            'hide_major_xtick_labels': self.hide_major_xtick_labels_var.get(), 'show_minor_xticks': self.show_minor_xticks_var.get(), 'xminor_tick_spacing': self.xminor_tick_spacing_var.get(),
            'peak_label_fontsize': self.peak_label_fontsize_var.get(), 'peak_label_offset': self.peak_label_offset_var.get()
        }

        bg_subtract_settings = {
            'enabled': self.bg_subtract_enabled_var.get(),
            'window_size': self.bg_subtract_window_var.get()
        }

        peak_detection_settings = {
            'enabled': self.peak_detection_enabled_var.get(),
            'min_height': self.peak_detection_height_var.get(),
            'min_prominence': self.peak_detection_prominence_var.get(),
            'min_width': self.peak_detection_width_var.get()
        }
        
        return {
            'plot_data_full': plot_data_full, 'threshold': threshold, 'x_range': (xmin, xmax), 
            'reference_peaks': reference_peaks, 'show_legend': self.show_legend_var.get(), 
            'stack': self.stack_plots_var.get(), 'spacing': spacing, 'appearance': appearance_settings,
            'bg_subtract_settings': bg_subtract_settings, 'peak_detection_settings': peak_detection_settings
        }

    def update_plot(self):
        settings = self._get_current_plot_settings()
        if not settings:
            self.ax.clear()
            self.ax.text(0.5, 0.5, "ファイルを選択するか、設定を確認してください", ha='center', va='center', transform=self.ax.transAxes)
            self.canvas.draw()
            return

        if not settings['plot_data_full']:
            self.ax.clear()
            self.ax.text(0.5, 0.5, "ファイルを選択してください", ha='center', va='center', transform=self.ax.transAxes)
            self.canvas.draw()
            return

        self.ax.clear()
        error_message = data_analyzer.draw_plot(ax=self.ax, **settings)
        if error_message: messagebox.showinfo("情報", error_message)
        self.fig.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.15)
        self.canvas.draw()
        
    def select_files(self):
        filepaths = filedialog.askopenfilenames(title="XRDファイルを選択", filetypes=[("RAS files", "*.ras"), ("All files", "*.*")])
        if filepaths:
            for fp in filepaths:
                if fp not in self.file_data:
                    angles, intensities = data_analyzer.parse_ras_file(fp)
                    if angles is None or intensities is None: messagebox.showwarning("警告", f"ファイル {os.path.basename(fp)} の読み込みに失敗しました。"); continue
                    self.parsed_data[fp] = (angles, intensities)
                    self.file_data[fp] = os.path.basename(fp); self.file_listbox.insert(tk.END, fp)
            if not self.file_listbox.curselection(): self.file_listbox.selection_set(tk.END); self.on_file_select(None)
            self.schedule_update()

    def remove_selected_file(self):
        selected_indices = self.file_listbox.curselection()
        if not selected_indices: return
        selected_filepath = self.file_listbox.get(selected_indices[0])
        if selected_filepath in self.file_data: del self.file_data[selected_filepath]
        if selected_filepath in self.parsed_data: del self.parsed_data[selected_filepath]
        self.file_listbox.delete(selected_indices[0])
        self.legend_name_entry.config(state="disabled"); self.legend_name_var.set("")
        if self.file_listbox.size() > 0:
            new_selection_index = min(selected_indices[0], self.file_listbox.size() - 1)
            self.file_listbox.selection_set(new_selection_index); self.on_file_select(None)
        self.schedule_update()

    def move_file_up(self):
        selected_indices = self.file_listbox.curselection()
        if not selected_indices: return
        idx = selected_indices[0]
        if idx > 0: filepath = self.file_listbox.get(idx); self.file_listbox.delete(idx); self.file_listbox.insert(idx - 1, filepath); self.file_listbox.selection_set(idx - 1); self.schedule_update()
        
    def move_file_down(self):
        selected_indices = self.file_listbox.curselection()
        if not selected_indices: return
        idx = selected_indices[0]
        if idx < self.file_listbox.size() - 1: filepath = self.file_listbox.get(idx); self.file_listbox.delete(idx); self.file_listbox.insert(idx + 1, filepath); self.file_listbox.selection_set(idx + 1); self.schedule_update()

    def preview_figure(self):
        settings = self._get_current_plot_settings()
        if not settings or not settings['plot_data_full']:
            messagebox.showwarning("警告", "プレビュー対象のデータがありません。", parent=self.master)
            return
        
        try:
            width = float(self.export_width_var.get())
            height = float(self.export_height_var.get())
            if width <= 0 or height <= 0: raise ValueError("サイズは正の値である必要があります。")
        except ValueError:
            messagebox.showerror("エラー", "幅または高さの値が不正です。", parent=self.master)
            return

        preview_window = tk.Toplevel(self.master)
        preview_window.title("エクスポートプレビュー")
        
        # Use a fixed DPI for the preview for predictability
        preview_dpi = 100
        fig = Figure(figsize=(width, height), dpi=preview_dpi)
        ax = fig.add_subplot(111)

        data_analyzer.draw_plot(ax=ax, **settings)
        fig.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.15)
        
        canvas = FigureCanvasTkAgg(fig, master=preview_window)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(canvas, preview_window)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Set window size based on figure size in pixels + toolbar
        preview_window.update_idletasks()
        width_px = int(width * preview_dpi)
        height_px = int(height * preview_dpi) + toolbar.winfo_height()
        preview_window.geometry(f"{width_px}x{height_px}")


    def save_figure(self):
        settings = self._get_current_plot_settings()
        if not settings or not settings['plot_data_full']:
            messagebox.showwarning("警告", "保存対象のデータがありません。", parent=self.master)
            return
            
        try:
            width = float(self.export_width_var.get()); height = float(self.export_height_var.get())
            if width <= 0 or height <= 0: raise ValueError("サイズは正の値である必要があります。")
        except ValueError:
            messagebox.showerror("エラー", "幅または高さの値が不正です。", parent=self.master)
            return
        
        default_filename = ""
        if self.file_listbox.size() > 0:
            first_filepath = self.file_listbox.get(0)
            legend_name = self.file_data.get(first_filepath, "")
            default_filename = os.path.splitext(legend_name)[0]

        filepath = filedialog.asksaveasfilename(title="グラフを保存", initialfile=default_filename, defaultextension=f".{self.export_format_var.get()}", filetypes=[(f"{self.export_format_var.get().upper()} files", f"*.{self.export_format_var.get()}"), ("All files", "*.*")], parent=self.master)
        if not filepath: return
        
        # Use a high DPI for saving the figure
        save_dpi = 300
        fig = Figure(figsize=(width, height), dpi=save_dpi)
        ax = fig.add_subplot(111)
        data_analyzer.draw_plot(ax=ax, **settings)
        # Adjust subplot parameters for the new figure
        fig.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.1)

        try:
            # Use bbox_inches='tight' to ensure labels are not cut off
            fig.savefig(filepath, dpi=save_dpi, bbox_inches='tight', transparent=True)
            messagebox.showinfo("成功", f"グラフを保存しました:\n{filepath}", parent=self.master)
        except Exception as e:
            messagebox.showerror("エラー", f"ファイルの保存中にエラーが発生しました:\n{e}", parent=self.master)

    def on_file_select(self, event):
        selected_indices = self.file_listbox.curselection()
        if not selected_indices: self.legend_name_entry.config(state="disabled"); self.legend_name_var.set(""); return
        selected_filepath = self.file_listbox.get(selected_indices[0]); self.legend_name_var.set(self.file_data.get(selected_filepath, "")); self.legend_name_entry.config(state="normal")

    def on_legend_name_change(self, *args):
        selected_indices = self.file_listbox.curselection()
        if selected_indices: selected_filepath = self.file_listbox.get(selected_indices[0]); self.file_data[selected_filepath] = self.legend_name_var.get(); self.schedule_update()

    def toggle_legend_visibility(self):
        if self.ax:
            legend = self.ax.get_legend()
            if legend: legend.set_visible(self.show_legend_var.get()); self.canvas.draw_idle()

    def schedule_update(self, *args):
        if self._debounce_job: self.master.after_cancel(self._debounce_job)
        self._debounce_job = self.master.after(250, self.update_plot)

    def calculate_d_spacing(self, *args):
        try:
            two_theta_deg = float(self.d_spacing_input_2theta_var.get())
            if two_theta_deg <= 0 or two_theta_deg >= 180: self.d_spacing_result_var.set("エラー: 2θは0-180の範囲で入力"); return
            theta_rad = math.radians(two_theta_deg / 2.0); lambda_coka1 = 1.78897
            d = lambda_coka1 / (2 * math.sin(theta_rad)); self.d_spacing_result_var.set(f"{d:.5f} Å")
        except (ValueError, TypeError): self.d_spacing_result_var.set("エラー: 有効な数値を入力してください")

    def copy_d_spacing(self, *args):
        try:
            result_str = self.d_spacing_result_var.get(); d_value = result_str.split(" ")[0]
            float(d_value); self.lc_input_d_var.set(d_value)
        except (ValueError, IndexError): pass

    def calculate_lattice_constant(self, *args):
        try:
            d = float(self.lc_input_d_var.get()); h = int(self.lc_h_var.get()); k = int(self.lc_k_var.get()); l = int(self.lc_l_var.get())
            if (h**2 + k**2 + l**2) == 0: self.lc_result_var.set("エラー: (h,k,l)は(0,0,0)にできません"); return
            a = d * math.sqrt(h**2 + k**2 + l**2); self.lc_result_var.set(f"a = {a:.5f} Å")
        except (ValueError, TypeError): self.lc_result_var.set("エラー: 有効な数値を入力してください")

if __name__ == '__main__':
    root = tk.Tk()
    app = XRDPlotter(master=root)
    app.mainloop()
