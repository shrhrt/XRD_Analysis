import tkinter as tk
from tkinter import filedialog, messagebox
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

        self.peak_name_entries = []
        self.peak_angle_entries = []
        self._debounce_job = None
        self.fig = None

        self.create_widgets()
        self.preset_peaks()

    def create_widgets(self):
        """GUIのウィジェットを作成し、配置する"""
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5)
        main_pane.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # --- 左側パネル (各種設定) ---
        left_panel = tk.Frame(main_pane, width=380)
        main_pane.add(left_panel, stretch="never")
        left_panel.rowconfigure(2, weight=1) # 参照ピークフレームを伸縮させる
        left_panel.columnconfigure(0, weight=1)

        # --- ファイル設定 (左パネル) ---
        file_frame = tk.LabelFrame(left_panel, text="ファイル設定")
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

        self.file_listbox = tk.Listbox(file_frame, selectmode=tk.EXTENDED, height=6)
        self.file_listbox.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        
        # --- グラフ設定 (左パネル) ---
        graph_settings_frame = tk.LabelFrame(left_panel, text="グラフ設定")
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

        self.xmin_var.trace_add("write", self.schedule_update)
        self.xmax_var.trace_add("write", self.schedule_update)
        self.threshold_var.trace_add("write", self.schedule_update)
        
        # --- 参照ピーク入力 (左パネル下部) ---
        container = tk.LabelFrame(left_panel, text="参照ピーク入力 (物質名と2θ値)")
        container.grid(row=2, column=0, sticky="nsew")
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)
        self.peak_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=self.peak_frame, anchor="nw")
        self.peak_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        self.peak_frame.columnconfigure(1, weight=1); self.peak_frame.columnconfigure(2, weight=1)
        tk.Label(self.peak_frame, text="物質名").grid(row=0, column=1, padx=5)
        tk.Label(self.peak_frame, text="2θ (degree)").grid(row=0, column=2, padx=5)
        for i in range(10):
            tk.Label(self.peak_frame, text=f"#{i+1}").grid(row=i+1, column=0, padx=5, pady=2, sticky="w")
            name_var = tk.StringVar()
            name_entry = tk.Entry(self.peak_frame, textvariable=name_var)
            name_entry.grid(row=i+1, column=1, padx=5, pady=2, sticky="ew")
            self.peak_name_entries.append(name_entry)
            name_var.trace_add("write", self.schedule_update)

            angle_var = tk.StringVar()
            angle_entry = tk.Entry(self.peak_frame, textvariable=angle_var)
            angle_entry.grid(row=i+1, column=2, padx=5, pady=2, sticky="ew")
            self.peak_angle_entries.append(angle_entry)
            angle_var.trace_add("write", self.schedule_update)

        # --- 右側パネル (グラフ表示) ---
        plot_panel = tk.Frame(main_pane)
        main_pane.add(plot_panel, stretch="always")

        self.canvas = FigureCanvasTkAgg(master=plot_panel)
        self.fig = self.canvas.figure
        self.ax = self.fig.add_subplot(111)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(self.canvas, plot_panel)
        toolbar.update()

    def select_files(self):
        filepaths = filedialog.askopenfilenames(
            title="XRDファイルを選択", filetypes=(("RAS files", "*.ras"), ("All files", "*.*"))
        )
        if filepaths:
            current_files = self.file_listbox.get(0, tk.END)
            for fp in filepaths:
                if fp not in current_files:
                    self.file_listbox.insert(tk.END, fp)
            self.schedule_update()

    def remove_selected_file(self):
        selected_indices = self.file_listbox.curselection()
        for i in reversed(selected_indices):
            self.file_listbox.delete(i)
        self.schedule_update()

    def preset_peaks(self):
        initial_peaks = {"LiTi2O4": "116.728", "Li4Ti5O12": "117.746"}
        for i, (name, angle) in enumerate(initial_peaks.items()):
            if i < len(self.peak_name_entries):
                self.peak_name_entries[i].insert(0, name)
                self.peak_angle_entries[i].insert(0, angle)

    def schedule_update(self, *args):
        """入力後、少し待ってからグラフを更新する"""
        if self._debounce_job:
            self.master.after_cancel(self._debounce_job)
        self._debounce_job = self.master.after(500, self.update_plot)

    def update_plot(self):
        """グラフを再描画する"""
        filepaths = self.file_listbox.get(0, tk.END)
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
                    reference_peaks.append({'name': name, 'angle': float(angle_str)})
                except ValueError:
                    pass # 不正な値は無視

        error_message = data_analyzer.draw_plot_on_axes(
            ax=self.ax,
            filepaths=filepaths,
            threshold=threshold,
            x_range=(xmin, xmax),
            reference_peaks=reference_peaks
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