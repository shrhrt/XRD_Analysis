import tkinter as tk
import os
from tkinter import ttk, filedialog, messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
import data_analyzer

class XRDPlotter(tk.Frame):
    """
    XRDデータをプロットするためのGUIアプリケーションクラス
    """
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("XRD Data Plotter")
        self.master.geometry("1280x720")
        self.pack(fill=tk.BOTH, expand=True)

        # 参照ピークのGUIウィジェットと関連変数を格納するリスト
        self.peak_name_entries = []
        self.peak_angle_entries = []
        self.peak_visible_vars = []
        self.peak_color_vars = []
        self.peak_style_vars = []
        self.peak_color_buttons = []

        self._debounce_job = None
        self.file_data = {} # {filepath: legend_name}
        self.fig = None

        self.create_widgets()
        self.preset_peaks()

    def create_widgets(self):
        """GUIのウィジェットを作成し、配置する"""
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5)
        main_pane.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # --- 左側パネル (各種設定) ---
        left_panel = tk.Frame(main_pane, width=400)
        main_pane.add(left_panel, stretch="never")
        left_panel.rowconfigure(0, weight=1)
        left_panel.columnconfigure(0, weight=1)

        # --- タブコントロール ---
        notebook = ttk.Notebook(left_panel)
        notebook.grid(row=0, column=0, sticky="nsew")

        plot_settings_tab = tk.Frame(notebook)
        export_tab = tk.Frame(notebook)
        notebook.add(plot_settings_tab, text="プロット設定")
        notebook.add(export_tab, text="エクスポート")

        plot_settings_tab.rowconfigure(2, weight=1) # 参照ピークフレームを伸縮させる
        plot_settings_tab.columnconfigure(0, weight=1)

        # --- ファイル設定 (左パネル) ---
        file_frame = tk.LabelFrame(plot_settings_tab, text="ファイル設定")
        file_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        file_frame.columnconfigure(0, weight=1)

        file_button_frame = tk.Frame(file_frame)
        file_button_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        file_button_frame.columnconfigure(0, weight=1)
        file_button_frame.columnconfigure(1, weight=1)

        select_button = tk.Button(file_button_frame, text="ファイルを選択", command=self.select_files)
        select_button.grid(row=0, column=0, sticky="ew", padx=(0, 2))
        remove_button = tk.Button(file_button_frame, text="選択したファイルを削除", command=self.remove_selected_file)
        remove_button.grid(row=0, column=1, sticky="ew", padx=(2, 0))

        listbox_frame = tk.Frame(file_frame)
        listbox_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        listbox_frame.rowconfigure(0, weight=1)
        listbox_frame.columnconfigure(0, weight=1)
        self.file_listbox = tk.Listbox(listbox_frame, selectmode=tk.SINGLE, height=6, exportselection=False)
        self.file_listbox.grid(row=0, column=0, sticky="nsew")
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_select)
        
        # ファイルリスト用のスクロールバー
        v_scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_listbox.config(yscrollcommand=v_scrollbar.set)
        h_scrollbar = tk.Scrollbar(listbox_frame, orient=tk.HORIZONTAL, command=self.file_listbox.xview)
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        self.file_listbox.config(xscrollcommand=h_scrollbar.set)
        
        # --- グラフ設定 (左パネル) ---
        graph_settings_frame = tk.LabelFrame(plot_settings_tab, text="グラフ設定")
        graph_settings_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        graph_settings_frame.columnconfigure(1, weight=1)

        self.xmin_var = tk.StringVar(value="30")
        tk.Label(graph_settings_frame, text="横軸 最小値:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.xmin_entry = tk.Entry(graph_settings_frame, textvariable=self.xmin_var)
        self.xmin_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        self.xmax_var = tk.StringVar(value="130")
        tk.Label(graph_settings_frame, text="横軸 最大値:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.xmax_entry = tk.Entry(graph_settings_frame, textvariable=self.xmax_var)
        self.xmax_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        self.threshold_var = tk.StringVar(value="0")
        tk.Label(graph_settings_frame, text="強度しきい値:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.threshold_entry = tk.Entry(graph_settings_frame, textvariable=self.threshold_var)
        self.threshold_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

        self.legend_name_var = tk.StringVar()
        tk.Label(graph_settings_frame, text="凡例名:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.legend_name_entry = tk.Entry(graph_settings_frame, textvariable=self.legend_name_var)
        self.legend_name_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=2)
        self.legend_name_entry.config(state="disabled")

        self.show_legend_var = tk.BooleanVar(value=True)
        show_legend_check = tk.Checkbutton(graph_settings_frame, text="凡例を表示する", variable=self.show_legend_var, command=self.toggle_legend_visibility)
        show_legend_check.grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=2)

        self.xmin_var.trace_add("write", self.schedule_update)
        self.xmax_var.trace_add("write", self.schedule_update)
        self.threshold_var.trace_add("write", self.schedule_update)
        self.legend_name_var.trace_add("write", self.on_legend_name_change)

        
        # --- 参照ピーク入力 (左パネル下部) ---
        container = tk.LabelFrame(plot_settings_tab, text="参照ピーク設定")
        container.grid(row=2, column=0, sticky="nsew")
        container.rowconfigure(0, weight=1); container.columnconfigure(0, weight=1)
        canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)
        self.peak_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=self.peak_frame, anchor="nw")
        self.peak_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Gridの列の重みを設定
        self.peak_frame.columnconfigure(2, weight=1) # 物質名
        self.peak_frame.columnconfigure(3, weight=1) # 2θ

        # ヘッダー
        tk.Label(self.peak_frame, text="表示").grid(row=0, column=1)
        tk.Label(self.peak_frame, text="物質名").grid(row=0, column=2)
        tk.Label(self.peak_frame, text="2θ").grid(row=0, column=3)
        tk.Label(self.peak_frame, text="色").grid(row=0, column=4)
        tk.Label(self.peak_frame, text="線種").grid(row=0, column=5)

        linestyle_map = {"実線": "-", "破線": "--", "点線": ":", "一点鎖線": "-."}
        
        for i in range(10):
            # --- 行番号 ---
            tk.Label(self.peak_frame, text=f"#{i+1}").grid(row=i+1, column=0, padx=(5,2), pady=2, sticky="w")
            
            # --- 表示チェックボックス ---
            vis_var = tk.BooleanVar(value=False)
            vis_check = tk.Checkbutton(self.peak_frame, variable=vis_var, command=self.schedule_update)
            vis_check.grid(row=i+1, column=1)
            self.peak_visible_vars.append(vis_var)

            # --- 物質名 ---
            name_var = tk.StringVar()
            name_entry = tk.Entry(self.peak_frame, textvariable=name_var)
            name_entry.grid(row=i+1, column=2, padx=2, pady=2, sticky="ew")
            self.peak_name_entries.append(name_entry)
            name_var.trace_add("write", self.schedule_update)

            # --- 2θ値 ---
            angle_var = tk.StringVar()
            angle_entry = tk.Entry(self.peak_frame, textvariable=angle_var)
            angle_entry.grid(row=i+1, column=3, padx=2, pady=2, sticky="ew")
            self.peak_angle_entries.append(angle_entry)
            angle_var.trace_add("write", self.schedule_update)

            # --- 色選択 ---
            color_var = tk.StringVar(value="#000000")
            color_button = tk.Button(self.peak_frame, text="■", width=2, relief=tk.SUNKEN,
                                     command=self._create_color_picker_command(i))
            color_button.grid(row=i+1, column=4, padx=2, pady=2)
            self.peak_color_vars.append(color_var)
            self.peak_color_buttons.append(color_button)

            # --- 線種 ---
            style_var = tk.StringVar(value=linestyle_map["破線"])
            style_combo = ttk.Combobox(self.peak_frame, values=list(linestyle_map.keys()), width=6, state="readonly")
            style_combo.set("破線") # 初期表示
            
            def create_on_style_selected(variable, combobox, style_map):
                def on_style_selected(event):
                    variable.set(style_map[combobox.get()])
                    self.schedule_update()
                return on_style_selected

            style_combo.bind("<<ComboboxSelected>>", create_on_style_selected(style_var, style_combo, linestyle_map))
            style_combo.grid(row=i+1, column=5, padx=(2,5), pady=2)
            self.peak_style_vars.append(style_var)

        # --- エクスポート設定 (エクスポートタブ) ---
        export_frame = tk.LabelFrame(export_tab, text="画像ファイルとして保存")
        export_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        export_frame.columnconfigure(1, weight=1)

        self.export_width_var = tk.StringVar(value="6")
        tk.Label(export_frame, text="幅 (inch):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        tk.Entry(export_frame, textvariable=self.export_width_var).grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        self.export_height_var = tk.StringVar(value="6")
        tk.Label(export_frame, text="高さ (inch):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        tk.Entry(export_frame, textvariable=self.export_height_var).grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        self.export_format_var = tk.StringVar(value="png")
        tk.Label(export_frame, text="形式:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        format_combo = ttk.Combobox(
            export_frame,
            textvariable=self.export_format_var,
            values=["png", "pdf"],
            state="readonly"
        )
        format_combo.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

        save_button = tk.Button(export_frame, text="グラフを保存", command=self.save_figure, font=("", 10, "bold"))
        save_button.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=(10, 5))

        # --- 右側パネル (グラフ表示) ---
        plot_panel = tk.Frame(main_pane)
        main_pane.add(plot_panel, stretch="always")

        self.canvas = FigureCanvasTkAgg(master=plot_panel)
        self.fig = self.canvas.figure
        self.ax = self.fig.add_subplot(111)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(self.canvas, plot_panel)
        toolbar.update()

    def _create_color_picker_command(self, index):
        """色選択ボタンのコマンドを生成するクロージャ"""
        from tkinter import colorchooser
        def command():
            # 現在の色を取得
            initial_color = self.peak_color_vars[index].get()
            # カラーチューザーを開く
            color_code = colorchooser.askcolor(title="色を選択", initialcolor=initial_color)
            # 色が選択された場合 (color_code は (rgb_tuple, hex_string) or (None, None))
            if color_code and color_code[1]:
                hex_color = color_code[1]
                self.peak_color_vars[index].set(hex_color)
                self.peak_color_buttons[index].config(fg=hex_color)
                self.schedule_update()
        return command


    def select_files(self):
        filepaths = filedialog.askopenfilenames(
            title="XRDファイルを選択", filetypes=(("RAS files", "*.ras"), ("All files", "*.*"))
        )
        if filepaths:
            for fp in filepaths:
                if fp not in self.file_data:
                    legend_name = os.path.basename(fp)
                    self.file_data[fp] = legend_name
                    self.file_listbox.insert(tk.END, fp)
            if self.file_listbox.curselection() == ():
                self.file_listbox.selection_set(tk.END)
                self.on_file_select(None)
            self.schedule_update()

    def remove_selected_file(self):
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            return
        
        selected_filepath = self.file_listbox.get(selected_indices[0])
        del self.file_data[selected_filepath]
        self.file_listbox.delete(selected_indices[0])

        self.legend_name_entry.config(state="disabled")
        self.legend_name_var.set("")
        
        if self.file_listbox.size() > 0:
            new_selection_index = min(selected_indices[0], self.file_listbox.size() - 1)
            self.file_listbox.selection_set(new_selection_index)
            self.on_file_select(None)
        
        self.schedule_update()

    def preset_peaks(self):
        initial_peaks = [
            {"name": "LiTi2O4", "angle": "116.728", "visible": True, "color": "#8B0000", "style": "--"},
            {"name": "Li4Ti5O12", "angle": "117.746", "visible": True, "color": "#00008B", "style": "--"},
            {"name": "TiO2", "angle": "25.3", "visible": False, "color": "#006400", "style": ":"},
        ]
        
        # tkinterの値からmatplotlibのスタイルへ変換する辞書の逆引き
        linestyle_map_inv = {"-": "実線", "--": "破線", ":": "点線", "-.": "一点鎖線"}

        for i, peak_data in enumerate(initial_peaks):
            if i < 10:
                self.peak_name_entries[i].insert(0, peak_data["name"])
                self.peak_angle_entries[i].insert(0, peak_data["angle"])
                self.peak_visible_vars[i].set(peak_data["visible"])
                self.peak_color_vars[i].set(peak_data["color"])
                self.peak_color_buttons[i].config(fg=peak_data["color"])
                self.peak_style_vars[i].set(peak_data["style"])
                
                # コンボボックスのテキスト表示を更新
                style_text = linestyle_map_inv.get(peak_data["style"])
                if style_text:
                    # `create_widgets`で生成されたコンボボックスのインスタンスを見つけて設定
                    # ちょっと技巧的だが、他に方法がない
                    for child in self.peak_frame.winfo_children():
                        if child.grid_info()["row"] == i + 1 and isinstance(child, ttk.Combobox):
                            child.set(style_text)
                            break

    def save_figure(self):
        """現在のグラフ（表示されている状態）を画像ファイルとして保存する"""
        if not self.ax.lines:
            messagebox.showwarning("警告", "保存対象のデータがありません。")
            return

        try:
            width = float(self.export_width_var.get())
            height = float(self.export_height_var.get())
            if width <= 0 or height <= 0:
                raise ValueError("サイズは正の値である必要があります。")
        except ValueError as e:
            messagebox.showerror("エラー", f"幅または高さの値が不正です: {e}")
            return

        file_format = self.export_format_var.get()
        filepath = filedialog.asksaveasfilename(
            title="グラフを保存",
            defaultextension=f".{file_format}",
            filetypes=[(f"{file_format.upper()} files", f"*.{file_format}"), ("All files", "*.*")]
        )

        if not filepath:
            return

        # 現在のFigureのサイズとDPIを保存
        original_size = self.fig.get_size_inches()
        original_dpi = self.fig.get_dpi()

        try:
            # 保存用にサイズとDPIを設定
            self.fig.set_size_inches(width, height)
            
            # PDF保存の場合、`bbox_inches='tight'` を使うと凡例がはみ出ないように調整される
            if file_format == 'pdf':
                self.fig.savefig(filepath, dpi=300, bbox_inches='tight')
            else:
                self.fig.savefig(filepath, dpi=300)
            
            messagebox.showinfo("成功", f"グラフを保存しました:\n{filepath}")

        except Exception as e:
            messagebox.showerror("エラー", f"ファイルの保存中にエラーが発生しました:\n{e}")

        finally:
            # FigureのサイズとDPIを元に戻す
            self.fig.set_size_inches(original_size)
            # GUI上の表示を再描画して元の見た目に戻す
            self.canvas.draw_idle()

    def on_file_select(self, event):
        """ファイルリストで項目が選択されたときに呼ばれる"""
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            self.legend_name_entry.config(state="disabled")
            self.legend_name_var.set("")
            return

        selected_filepath = self.file_listbox.get(selected_indices[0])
        self.legend_name_var.set(self.file_data.get(selected_filepath, ""))
        self.legend_name_entry.config(state="normal")

    def on_legend_name_change(self, *args):
        selected_indices = self.file_listbox.curselection()
        if selected_indices:
            selected_filepath = self.file_listbox.get(selected_indices[0])
            self.file_data[selected_filepath] = self.legend_name_var.get()
            self.schedule_update()

    def toggle_legend_visibility(self):
        """凡例の表示/非表示を切り替える"""
        legend = self.ax.get_legend()
        if legend:
            legend.set_visible(self.show_legend_var.get())
            self.canvas.draw_idle()

    def schedule_update(self, *args):
        """入力後、少し待ってからグラフを更新する"""
        if self._debounce_job:
            self.master.after_cancel(self._debounce_job)
        self._debounce_job = self.master.after(500, self.update_plot)

    def update_plot(self):
        """グラフを再描画する"""
        filepaths = list(self.file_data.keys())
        if not filepaths:
            self.ax.clear()
            self.ax.text(0.5, 0.5, "ファイルを選択してください", ha='center', va='center', transform=self.ax.transAxes)
            self.canvas.draw()
            return

        try:
            threshold = float(self.threshold_var.get()) if self.threshold_var.get() else 0.0
        except ValueError:
            return

        try:
            xmin = float(self.xmin_var.get()) if self.xmin_var.get() else None
            xmax = float(self.xmax_var.get()) if self.xmax_var.get() else None
            if xmin is not None and xmax is not None and xmin >= xmax:
                messagebox.showwarning("警告", "横軸の最小値は最大値より小さくしてください。")
                return
        except ValueError:
            messagebox.showwarning("警告", "横軸の範囲には数値を入力してください。")
            return

        reference_peaks = []
        for i in range(10):
            name = self.peak_name_entries[i].get().strip()
            angle_str = self.peak_angle_entries[i].get().strip()
            if name and angle_str:
                try:
                    reference_peaks.append({
                        'name': name,
                        'angle': float(angle_str),
                        'visible': self.peak_visible_vars[i].get(),
                        'color': self.peak_color_vars[i].get(),
                        'linestyle': self.peak_style_vars[i].get()
                    })
                except ValueError:
                    pass # 不正な値は無視

        plot_data = []
        for fp in self.file_listbox.get(0, tk.END):
            if fp in self.file_data:
                plot_data.append({'filepath': fp, 'label': self.file_data[fp]})

        error_message = data_analyzer.draw_plot_on_axes(
            ax=self.ax,
            plot_data=plot_data,
            threshold=threshold,
            x_range=(xmin, xmax),
            reference_peaks=reference_peaks,
            show_legend=self.show_legend_var.get()
        )

        # tight_layout() はテキストがはみ出すと警告を出すため、
        # subplots_adjust() で手動で余白を調整する
        self.fig.subplots_adjust(left=0.08, right=0.95, top=0.95, bottom=0.1)

        self.canvas.draw()

        if error_message:
            messagebox.showinfo("情報", error_message)

if __name__ == '__main__':
    root = tk.Tk()
    app = XRDPlotter(master=root)
    app.mainloop()