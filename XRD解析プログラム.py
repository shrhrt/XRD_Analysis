import tkinter as tk
import os
from tkinter import ttk, filedialog, messagebox
import numpy as np
import math

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
import data_analyzer

class XRDPlotter(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("XRD Data Plotter")
        self.master.geometry("1280x720")
        self.pack(fill=tk.BOTH, expand=True)

        # --- Variables ---
        # Peak settings (lists)
        self.peak_name_vars = []
        self.peak_angle_vars = []
        self.peak_visible_vars = []
        self.peak_color_vars = []
        self.peak_style_vars = []
        self.peak_color_buttons = []
        
        # Plot settings (individual vars)
        self.xmin_var = tk.StringVar(value="30")
        self.xmax_var = tk.StringVar(value="130")
        self.threshold_var = tk.StringVar(value="1")
        self.legend_name_var = tk.StringVar()
        self.show_legend_var = tk.BooleanVar(value=True)
        self.stack_plots_var = tk.BooleanVar(value=False)
        self.plot_spacing_var = tk.DoubleVar(value=3)

        # Appearance settings (individual vars)
        self.xlabel_var = tk.StringVar(value="2θ/ω (degree)")
        self.ylabel_var = tk.StringVar(value="Log Intensity (arb. Units)")
        self.axis_label_fontsize_var = tk.DoubleVar(value=20)
        self.tick_label_fontsize_var = tk.DoubleVar(value=16)
        self.legend_fontsize_var = tk.DoubleVar(value=10)
        self.plot_linewidth_var = tk.DoubleVar(value=1.0)
        self.tick_direction_var = tk.StringVar(value='in')
        self.xaxis_major_tick_spacing_var = tk.DoubleVar(value=10)
        self.show_grid_var = tk.BooleanVar(value=False)
        self.ytop_padding_factor_var = tk.DoubleVar(value=1.5)
        self.hide_major_xtick_labels_var = tk.BooleanVar(value=False)
        self.show_minor_xticks_var = tk.BooleanVar(value=False)
        self.xminor_tick_spacing_var = tk.DoubleVar(value=1.0)
        
        # Analysis tools (individual vars)
        self.d_spacing_input_2theta_var = tk.StringVar()
        self.d_spacing_result_var = tk.StringVar(value="d-spacing (Å)")
        self.lc_input_d_var = tk.StringVar()
        self.lc_h_var = tk.StringVar(value="1")
        self.lc_k_var = tk.StringVar(value="1")
        self.lc_l_var = tk.StringVar(value="1")
        self.lc_result_var = tk.StringVar(value="a = ?")

        # Export settings (individual vars)
        self.export_width_var = tk.StringVar(value="6")
        self.export_height_var = tk.StringVar(value="6")
        self.export_format_var = tk.StringVar(value="png")
        
        # Internal state
        self._debounce_job = None
        self.file_data = {}
        self.fig = None
        self.ax = None

        self.create_widgets()
        self.preset_peaks()

    def _toggle_spacing_widget(self, *args):
        if self.stack_plots_var.get():
            self.spacing_label.grid()
            self.spacing_entry.grid()
        else:
            self.spacing_label.grid_remove()
            self.spacing_entry.grid_remove()
        self.schedule_update()

    def _toggle_minor_xticks_widgets(self, *args):
        if self.show_minor_xticks_var.get():
            self.xminor_tick_spacing_label.grid()
            self.xminor_tick_spacing_entry.grid()
        else:
            self.xminor_tick_spacing_label.grid_remove()
            self.xminor_tick_spacing_entry.grid_remove()
        self.schedule_update()

    def create_widgets(self):
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5)
        main_pane.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        left_panel = tk.Frame(main_pane, width=480)
        main_pane.add(left_panel, stretch="never")
        left_panel.rowconfigure(0, weight=1)
        left_panel.columnconfigure(0, weight=1)

        notebook = ttk.Notebook(left_panel)
        notebook.grid(row=0, column=0, sticky="nsew")

        plot_settings_tab = tk.Frame(notebook)
        appearance_tab = tk.Frame(notebook)
        analysis_tab = tk.Frame(notebook)
        export_tab = tk.Frame(notebook)
        notebook.add(plot_settings_tab, text="プロット設定")
        notebook.add(appearance_tab, text="外観設定")
        notebook.add(analysis_tab, text="解析ツール")
        notebook.add(export_tab, text="エクスポート")
        
        self.build_plot_settings_tab(plot_settings_tab)
        self.build_appearance_tab(appearance_tab)
        self.build_analysis_tab(analysis_tab)
        self.build_export_tab(export_tab)

        plot_panel = tk.Frame(main_pane)
        main_pane.add(plot_panel, stretch="always")
        self.canvas = FigureCanvasTkAgg(master=plot_panel)
        self.fig = self.canvas.figure
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(self.canvas, plot_panel)
        toolbar.update()
        
        self._toggle_spacing_widget()
        self._toggle_minor_xticks_widgets()

    def build_plot_settings_tab(self, tab):
        tab.rowconfigure(2, weight=1)
        tab.columnconfigure(0, weight=1)
        
        file_frame = tk.LabelFrame(tab, text="ファイル設定")
        file_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        file_frame.columnconfigure(0, weight=1)
        file_button_frame = tk.Frame(file_frame)
        file_button_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        file_button_frame.columnconfigure(0, weight=1)
        file_button_frame.columnconfigure(1, weight=1)
        file_button_frame.columnconfigure(2, weight=1)
        
        tk.Button(file_button_frame, text="ファイルを選択", command=self.select_files).grid(row=0, column=0, sticky="ew", padx=(0, 2))
        tk.Button(file_button_frame, text="選択したファイルを削除", command=self.remove_selected_file).grid(row=0, column=1, sticky="ew", padx=(2, 0))
        
        reorder_frame = tk.Frame(file_button_frame)
        reorder_frame.grid(row=0, column=2, rowspan=2, padx=(5,0))
        tk.Button(reorder_frame, text="↑", command=self.move_file_up).pack(fill='x')
        tk.Button(reorder_frame, text="↓", command=self.move_file_down).pack(fill='x')
        
        listbox_frame = tk.Frame(file_frame)
        listbox_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=(0, 5))
        listbox_frame.rowconfigure(0, weight=1)
        listbox_frame.columnconfigure(0, weight=1)
        self.file_listbox = tk.Listbox(listbox_frame, selectmode=tk.SINGLE, height=6, exportselection=False)
        self.file_listbox.grid(row=0, column=0, sticky="nsew")
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_select)
        v_scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_listbox.config(yscrollcommand=v_scrollbar.set)
        h_scrollbar = tk.Scrollbar(listbox_frame, orient=tk.HORIZONTAL, command=self.file_listbox.xview)
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        self.file_listbox.config(xscrollcommand=h_scrollbar.set)

        graph_settings_frame = tk.LabelFrame(tab, text="グラフ設定")
        graph_settings_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        graph_settings_frame.columnconfigure(1, weight=1)
        
        tk.Label(graph_settings_frame, text="横軸 最小値:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.xmin_entry = tk.Entry(graph_settings_frame, textvariable=self.xmin_var)
        self.xmin_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        tk.Label(graph_settings_frame, text="横軸 最大値:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.xmax_entry = tk.Entry(graph_settings_frame, textvariable=self.xmax_var)
        self.xmax_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        
        tk.Label(graph_settings_frame, text="強度しきい値:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.threshold_entry = tk.Entry(graph_settings_frame, textvariable=self.threshold_var)
        self.threshold_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        
        tk.Label(graph_settings_frame, text="凡例名:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.legend_name_entry = tk.Entry(graph_settings_frame, textvariable=self.legend_name_var, state="disabled")
        self.legend_name_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=2)
        
        self.show_legend_check = tk.Checkbutton(graph_settings_frame, text="凡例を表示する", variable=self.show_legend_var, command=self.toggle_legend_visibility)
        self.show_legend_check.grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        
        tk.Checkbutton(graph_settings_frame, text="グラフを縦に並べる", variable=self.stack_plots_var, command=self._toggle_spacing_widget).grid(row=5, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        
        self.spacing_label = tk.Label(graph_settings_frame, text="グラフの間隔 (10^n):")
        self.spacing_label.grid(row=6, column=0, sticky="w", padx=5, pady=2)
        self.spacing_entry = tk.Scale(graph_settings_frame, variable=self.plot_spacing_var, orient=tk.HORIZONTAL, from_=0, to=5, resolution=0.1, command=self.schedule_update)
        self.spacing_entry.grid(row=6, column=1, sticky="ew", padx=5, pady=2)
        
        self.xmin_entry.bind("<FocusOut>", self.schedule_update)
        self.xmin_entry.bind("<Return>", self.schedule_update)
        self.xmax_entry.bind("<FocusOut>", self.schedule_update)
        self.xmax_entry.bind("<Return>", self.schedule_update)
        self.threshold_var.trace_add("write", self.schedule_update)
        self.legend_name_var.trace_add("write", self.on_legend_name_change)

        container = tk.LabelFrame(tab, text="参照ピーク設定"); container.grid(row=2, column=0, sticky="nsew"); container.rowconfigure(0, weight=1); container.columnconfigure(0, weight=1)
        canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0); canvas.grid(row=0, column=0, sticky="nsew"); scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview); scrollbar.grid(row=0, column=1, sticky="ns"); canvas.configure(yscrollcommand=scrollbar.set); self.peak_frame = tk.Frame(canvas); canvas.create_window((0, 0), window=self.peak_frame, anchor="nw"); self.peak_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))); self.peak_frame.columnconfigure(2, weight=1); self.peak_frame.columnconfigure(3, weight=1)
        tk.Label(self.peak_frame, text="表示").grid(row=0, column=1); tk.Label(self.peak_frame, text="物質名").grid(row=0, column=2); tk.Label(self.peak_frame, text="2θ").grid(row=0, column=3); tk.Label(self.peak_frame, text="色").grid(row=0, column=4); tk.Label(self.peak_frame, text="線種").grid(row=0, column=5)
        linestyle_map = {"実線": "-", "破線": "--", "点線": ":", "一点鎖線": "-."}
        for i in range(10):
            tk.Label(self.peak_frame, text=f"#{i+1}").grid(row=i+1, column=0, padx=(5,2), pady=2, sticky="w"); vis_var = tk.BooleanVar(value=False); tk.Checkbutton(self.peak_frame, variable=vis_var, command=self.schedule_update).grid(row=i+1, column=1); self.peak_visible_vars.append(vis_var); name_var = tk.StringVar(); tk.Entry(self.peak_frame, textvariable=name_var).grid(row=i+1, column=2, padx=2, pady=2, sticky="ew"); self.peak_name_vars.append(name_var); name_var.trace_add("write", self.schedule_update); angle_var = tk.StringVar(); tk.Entry(self.peak_frame, textvariable=angle_var).grid(row=i+1, column=3, padx=2, pady=2, sticky="ew"); self.peak_angle_vars.append(angle_var); angle_var.trace_add("write", self.schedule_update); color_var = tk.StringVar(value="#000000"); color_button = tk.Button(self.peak_frame, text="■", width=2, relief=tk.SUNKEN, command=self._create_color_picker_command(i)); color_button.grid(row=i+1, column=4, padx=2, pady=2); self.peak_color_vars.append(color_var); self.peak_color_buttons.append(color_button); style_var = tk.StringVar(value=linestyle_map["破線"]); style_combo = ttk.Combobox(self.peak_frame, values=list(linestyle_map.keys()), width=6, state="readonly"); style_combo.set("破線"); style_combo.bind("<<ComboboxSelected>>", lambda e, v=style_var, c=style_combo, m=linestyle_map: (v.set(m[c.get()]), self.schedule_update())); style_combo.grid(row=i+1, column=5, padx=(2,5), pady=2); self.peak_style_vars.append(style_var)

    def build_appearance_tab(self, tab):
        appearance_frame = tk.Frame(tab, padx=10, pady=10); appearance_frame.pack(fill="x"); appearance_frame.columnconfigure(1, weight=1)
        def create_row(parent, label_text, var, row, widget_class=tk.Entry, **widget_args):
            tk.Label(parent, text=label_text).grid(row=row, column=0, sticky="w", pady=2)
            widget = widget_class(parent, textvariable=var, **widget_args)
            widget.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
            if isinstance(widget, (ttk.Spinbox, tk.Scale)): widget.configure(command=lambda *args: self.schedule_update())
            elif isinstance(widget, tk.Entry): var.trace_add("write", self.schedule_update)
        create_row(appearance_frame, "X軸ラベル:", self.xlabel_var, 0); create_row(appearance_frame, "Y軸ラベル:", self.ylabel_var, 1)
        create_row(appearance_frame, "軸ラベルフォントサイズ:", self.axis_label_fontsize_var, 2, ttk.Spinbox, from_=1, to=100)
        create_row(appearance_frame, "目盛りフォントサイズ:", self.tick_label_fontsize_var, 3, ttk.Spinbox, from_=1, to=100)
        create_row(appearance_frame, "凡例フォントサイズ:", self.legend_fontsize_var, 4, ttk.Spinbox, from_=1, to=100)
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
        analysis_frame = tk.Frame(tab, padx=10, pady=10); analysis_frame.pack(fill="x")
        d_spacing_frame = tk.LabelFrame(analysis_frame, text="d値計算ツール"); d_spacing_frame.pack(fill="x", pady=5); d_spacing_frame.columnconfigure(1, weight=1)
        tk.Label(d_spacing_frame, text="ブラッグの式: nλ = 2d sin(θ)").grid(row=0, column=0, columnspan=3, sticky="w", padx=5)
        tk.Label(d_spacing_frame, text="定数: X線=Co Kα1 (λ=1.78897 Å), n=1").grid(row=1, column=0, columnspan=3, sticky="w", padx=5)
        tk.Label(d_spacing_frame, text="2θ (degree):").grid(row=2, column=0, sticky="w", padx=5, pady=5); d_input_entry = tk.Entry(d_spacing_frame, textvariable=self.d_spacing_input_2theta_var); d_input_entry.grid(row=2, column=1, sticky="ew", padx=5); tk.Button(d_spacing_frame, text="計算", command=self.calculate_d_spacing).grid(row=2, column=2, padx=5)
        tk.Label(d_spacing_frame, textvariable=self.d_spacing_result_var, relief="sunken").grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5); d_input_entry.bind("<Return>", self.calculate_d_spacing)
        lc_frame = tk.LabelFrame(analysis_frame, text="格子定数計算ツール (立方晶のみ)"); lc_frame.pack(fill="x", pady=5); lc_frame.columnconfigure(1, weight=1)
        tk.Label(lc_frame, text="式: a = d * √(h² + k² + l²)").grid(row=0, column=0, columnspan=3, sticky="w", padx=5)
        tk.Label(lc_frame, text="d-spacing (Å):").grid(row=1, column=0, sticky="w", padx=5, pady=5); lc_d_entry = tk.Entry(lc_frame, textvariable=self.lc_input_d_var); lc_d_entry.grid(row=1, column=1, sticky="ew", padx=5); tk.Button(lc_frame, text="コピー", command=self.copy_d_spacing).grid(row=1, column=2, padx=5)
        hkl_frame = tk.Frame(lc_frame); hkl_frame.grid(row=2, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        tk.Label(hkl_frame, text="面指数 (h, k, l):").pack(side="left"); tk.Entry(hkl_frame, textvariable=self.lc_h_var, width=5).pack(side="left"); tk.Entry(hkl_frame, textvariable=self.lc_k_var, width=5).pack(side="left"); tk.Entry(hkl_frame, textvariable=self.lc_l_var, width=5).pack(side="left")
        tk.Button(lc_frame, text="計算", command=self.calculate_lattice_constant).grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        tk.Label(lc_frame, textvariable=self.lc_result_var, relief="sunken").grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

    def build_export_tab(self, tab):
        export_frame = tk.LabelFrame(tab, text="画像ファイルとして保存"); export_frame.pack(fill="x", padx=10, pady=10)
        export_frame.columnconfigure(1, weight=1)
        self.export_width_var = tk.StringVar(value="6"); tk.Label(export_frame, text="幅 (inch):").grid(row=0, column=0, sticky="w", padx=5, pady=2); tk.Entry(export_frame, textvariable=self.export_width_var).grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        tk.Label(export_frame, text="高さ (inch):").grid(row=1, column=0, sticky="w", padx=5, pady=2); tk.Entry(export_frame, textvariable=self.export_height_var).grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        tk.Label(export_frame, text="形式:").grid(row=2, column=0, sticky="w", padx=5, pady=2); ttk.Combobox(export_frame, textvariable=self.export_format_var, values=["png", "pdf"], state="readonly").grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        tk.Button(export_frame, text="グラフを保存", command=self.save_figure, font=("", 10, "bold")).grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=(10, 5))

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
            a = d * math.sqrt(h**2 + k**2 + l**2); self.lc_result_var.set(f"a = {a:.5f} Å")
        except (ValueError, TypeError): self.lc_result_var.set("エラー: 有効な数値を入力してください")
            
    def _create_color_picker_command(self, index):
        from tkinter import colorchooser
        def command():
            color_code = colorchooser.askcolor(title="色を選択", initialcolor=self.peak_color_vars[index].get())
            if color_code and color_code[1]: self.peak_color_vars[index].set(color_code[1]); self.peak_color_buttons[index].config(fg=color_code[1]); self.schedule_update()
        return command

    def update_plot(self):
        filepaths = self.file_listbox.get(0, tk.END)
        if not filepaths:
            if self.ax: self.ax.clear()
            else: self.ax = self.fig.add_subplot(111)
            self.ax.text(0.5, 0.5, "ファイルを選択してください", ha='center', va='center', transform=self.ax.transAxes); self.canvas.draw(); return
        try:
            threshold = float(self.threshold_var.get()) if self.threshold_var.get() else 0.0
            spacing = self.plot_spacing_var.get()
            xmin = float(self.xmin_var.get()) if self.xmin_var.get() else None
            xmax = float(self.xmax_var.get()) if self.xmax_var.get() else None
            if xmin is not None and xmax is not None and xmin >= xmax: messagebox.showwarning("警告", "横軸の最小値は最大値より小さくしてください。"); return
        except ValueError: messagebox.showwarning("警告", "グラフ設定の数値が不正です。"); return
        reference_peaks = [{'name': self.peak_name_vars[i].get().strip(), 'angle': float(self.peak_angle_vars[i].get().strip()), 'visible': self.peak_visible_vars[i].get(), 'color': self.peak_color_vars[i].get(), 'linestyle': self.peak_style_vars[i].get()} for i in range(10) if self.peak_name_vars[i].get().strip() and self.peak_angle_vars[i].get().strip()]
        plot_data = [{'filepath': fp, 'label': self.file_data[fp]} for fp in filepaths if fp in self.file_data]
        appearance_settings = {
            'xlabel': self.xlabel_var.get(), 'ylabel': self.ylabel_var.get(), 
            'axis_label_fontsize': self.axis_label_fontsize_var.get(), 
            'tick_label_fontsize': self.tick_label_fontsize_var.get(), 
            'legend_fontsize': self.legend_fontsize_var.get(), 
            'linewidth': self.plot_linewidth_var.get(), 
            'tick_direction': self.tick_direction_var.get(), 
            'xaxis_major_tick_spacing': self.xaxis_major_tick_spacing_var.get(), 
            'show_grid': self.show_grid_var.get(),
            'ytop_padding_factor': self.ytop_padding_factor_var.get(),
            'hide_major_xtick_labels': self.hide_major_xtick_labels_var.get(),
            'show_minor_xticks': self.show_minor_xticks_var.get(),
            'xminor_tick_spacing': self.xminor_tick_spacing_var.get()
        }

        self.fig.clear(); self.ax = self.fig.add_subplot(111)
        error_message = data_analyzer.draw_plot(ax=self.ax, plot_data=plot_data, threshold=threshold, x_range=(xmin, xmax), reference_peaks=reference_peaks, show_legend=self.show_legend_var.get(), stack=self.stack_plots_var.get(), spacing=spacing, appearance=appearance_settings)
        if error_message: messagebox.showinfo("情報", error_message)
        self.fig.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.15)
        self.canvas.draw()
        
    def select_files(self):
        filepaths = filedialog.askopenfilenames(title="XRDファイルを選択", filetypes=(("RAS files", "*.ras"), ("All files", "*.*")))
        if filepaths:
            for fp in filepaths:
                if fp not in self.file_data: self.file_data[fp] = os.path.basename(fp); self.file_listbox.insert(tk.END, fp)
            if not self.file_listbox.curselection(): self.file_listbox.selection_set(tk.END); self.on_file_select(None)
            self.schedule_update()

    def remove_selected_file(self):
        selected_indices = self.file_listbox.curselection()
        if not selected_indices: return
        selected_filepath = self.file_listbox.get(selected_indices[0]); del self.file_data[selected_filepath]; self.file_listbox.delete(selected_indices[0])
        self.legend_name_entry.config(state="disabled"); self.legend_name_var.set("")
        if self.file_listbox.size() > 0: new_selection_index = min(selected_indices[0], self.file_listbox.size() - 1); self.file_listbox.selection_set(new_selection_index); self.on_file_select(None)
        self.schedule_update()

    def move_file_up(self):
        selected_indices = self.file_listbox.curselection();
        if not selected_indices: return
        idx = selected_indices[0]
        if idx > 0: filepath = self.file_listbox.get(idx); self.file_listbox.delete(idx); self.file_listbox.insert(idx - 1, filepath); self.file_listbox.selection_set(idx - 1); self.schedule_update()
        
    def move_file_down(self):
        selected_indices = self.file_listbox.curselection();
        if not selected_indices: return
        idx = selected_indices[0]
        if idx < self.file_listbox.size() - 1: filepath = self.file_listbox.get(idx); self.file_listbox.delete(idx); self.file_listbox.insert(idx + 1, filepath); self.file_listbox.selection_set(idx + 1); self.schedule_update()

    def preset_peaks(self):
        initial_peaks = [{"name": "LiTi2O4", "angle": "116.728", "visible": False, "color": "#8B0000", "style": "--"}, {"name": "Li4Ti5O12", "angle": "117.746", "visible": False, "color": "#00008B", "style": "--"}, {"name": "TiO2", "angle": "25.3", "visible": False, "color": "#006400", "style": ":"}]
        linestyle_map_inv = {"-": "実線", "--": "破線", ":": "点線", "-.": "一点鎖線"}
        for i, peak_data in enumerate(initial_peaks):
            if i < 10:
                self.peak_name_vars[i].set(peak_data["name"]); self.peak_angle_vars[i].set(peak_data["angle"]); self.peak_visible_vars[i].set(peak_data["visible"]); self.peak_color_vars[i].set(peak_data["color"]); self.peak_color_buttons[i].config(fg=peak_data["color"]); self.peak_style_vars[i].set(peak_data["style"])
                style_text = linestyle_map_inv.get(peak_data["style"])
                if style_text:
                    for child in self.peak_frame.winfo_children():
                        if child.grid_info()["row"] == i + 1 and isinstance(child, ttk.Combobox): child.set(style_text); break

    def save_figure(self):
        if not self.ax or not self.ax.lines:
            messagebox.showwarning("警告", "保存対象のデータがありません。")
            return
        try:
            width = float(self.export_width_var.get())
            height = float(self.export_height_var.get())
            if width <= 0 or height <= 0:
                raise ValueError("サイズは正の値である必要があります。")
        except ValueError:
            messagebox.showerror("エラー", "幅または高さの値が不正です。")
            return
            
        filepath = filedialog.asksaveasfilename(title="グラフを保存",defaultextension=f".{self.export_format_var.get()}", filetypes=[(f"{self.export_format_var.get().upper()} files", f"*.{self.export_format_var.get()}"), ("All files", "*.*")])
        if not filepath:
            return
            
        original_size = self.fig.get_size_inches()
        try:
            self.fig.set_size_inches(width, height)
            self.fig.savefig(filepath, dpi=300, bbox_inches='tight')
            messagebox.showinfo("成功", f"グラフを保存しました:\n{filepath}")
        except Exception as e:
            messagebox.showerror("エラー", f"ファイルの保存中にエラーが発生しました:\n{e}")
        finally:
            self.fig.set_size_inches(original_size)
            self.canvas.draw_idle()

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
            if legend:
                legend.set_visible(self.show_legend_var.get())
                self.canvas.draw_idle()

    def schedule_update(self, *args):
        if self._debounce_job: self.master.after_cancel(self._debounce_job)
        self._debounce_job = self.master.after(250, self.update_plot)

if __name__ == '__main__':
    root = tk.Tk()
    app = XRDPlotter(master=root)
    app.mainloop()
