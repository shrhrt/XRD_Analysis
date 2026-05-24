import tkinter as tk
import os
import logging
from tkinter import ttk
from matplotlib.figure import Figure
from tkinterdnd2 import DND_FILES

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from core.app_model import AppStateModel
import sv_ttk
from ui.tab_plot import PlotSettingsTab
from ui.tab_reference import ReferencePeaksTab
from ui.tab_analysis import AnalysisTab
from ui.tab_appearance import AppearanceTab
from ui.tab_export import ExportTab
from ui.handlers.file_handler import FileHandler
from ui.handlers.settings_handler import SettingsHandler
from ui.handlers.plot_handler import PlotHandler
from ui.handlers.fit_handler import FitHandler
from ui.tab_fit import FitTab
from ui.theory_dialog import show_theory_dialog

logger = logging.getLogger(__name__)


class MainWindow(ttk.Frame):
    """アプリケーションのメインウィンドウと全体のイベントを管理するクラス"""

    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("XRD Data Plotter")
        self.master.geometry("1280x720")
        self.pack(fill=tk.BOTH, expand=True)

        self.model = AppStateModel()
        self.peak_color_buttons = []  # UI要素なのでこちらに残す

        self.recent_files = []
        # ユーザーのホームディレクトリの下に専用フォルダを作成する。
        config_dir = os.path.join(os.path.expanduser("~"), ".xrd_plotter")
        os.makedirs(config_dir, exist_ok=True)
        self.config_file = os.path.join(config_dir, "xrd_app_config.json")
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self._debounce_job, self.file_data, self.parsed_data = None, {}, {}

        # 入力検証コマンドの登録
        self.vcmd_float = (self.register(self._validate_float), "%P")

        self.fig = Figure(figsize=(6, 4))
        self.ax = self.fig.add_subplot(111)

        self.file_handler = FileHandler(self, self.model)
        self.settings_handler = SettingsHandler(self, self.model)
        self.plot_handler = PlotHandler(self, self.model)
        self.fit_handler = FitHandler(self, self.model)

        self.create_menu()
        self.create_widgets()
        self.settings_handler.load_app_config()

    def toggle_theme(self):
        if sv_ttk.get_theme() == "dark":
            sv_ttk.set_theme("light")
            self._view_menu.entryconfig(0, label="ダークモードに切り替え")
        else:
            sv_ttk.set_theme("dark")
            self._view_menu.entryconfig(0, label="ライトモードに切り替え")

    def create_menu(self):
        self.menubar = tk.Menu(self.master)
        self.master.config(menu=self.menubar)

        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="ファイル", menu=file_menu)

        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="最近開いたファイル", menu=self.recent_menu)
        self.file_handler.update_recent_menu()
        file_menu.add_separator()
        file_menu.add_command(
            label="設定を読み込む...", command=self.settings_handler.load_settings
        )
        file_menu.add_command(
            label="設定を保存...", command=self.settings_handler.save_settings
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="グラフを画像として保存...", command=self.plot_handler.save_figure
        )
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.on_closing)

        self._view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="表示", menu=self._view_menu)
        self._view_menu.add_command(label="ダークモードに切り替え", command=self.toggle_theme)
        self._view_menu.add_separator()
        self._restore_var = tk.BooleanVar(value=self.settings_handler.get_restore_on_startup())
        self._view_menu.add_checkbutton(
            label="起動時に前回のセッションを復元する",
            variable=self._restore_var,
            command=lambda: self.settings_handler.set_restore_on_startup(self._restore_var.get()),
        )

        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="ヘルプ", menu=help_menu)
        help_menu.add_command(
            label="理論・計算式の解説",
            command=lambda: show_theory_dialog(self.master),
        )

    def create_widgets(self):
        main_pane = tk.PanedWindow(
            self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5
        )
        main_pane.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        left_panel = ttk.Frame(main_pane, width=480)
        main_pane.add(left_panel, stretch="never")
        left_panel.rowconfigure(0, weight=1)
        left_panel.columnconfigure(0, weight=1)

        notebook = ttk.Notebook(left_panel)
        notebook.grid(row=0, column=0, sticky="nsew")
        (
            plot_settings_tab,
            reference_peaks_tab,
            appearance_tab,
            analysis_tab,
            fit_tab,
            export_tab,
        ) = (
            ttk.Frame(notebook),
            ttk.Frame(notebook),
            ttk.Frame(notebook),
            ttk.Frame(notebook),
            ttk.Frame(notebook),
            ttk.Frame(notebook),
        )
        notebook.add(plot_settings_tab, text="プロット設定")
        notebook.add(reference_peaks_tab, text="参照ピーク")
        notebook.add(appearance_tab, text="外観設定")
        notebook.add(analysis_tab, text="解析ツール")
        notebook.add(fit_tab, text="ピークフィット")
        notebook.add(export_tab, text="エクスポート")

        PlotSettingsTab(plot_settings_tab, self)
        ReferencePeaksTab(reference_peaks_tab, self)
        AppearanceTab(appearance_tab, self)
        AnalysisTab(analysis_tab, self)
        self.fit_tab = FitTab(fit_tab, self)
        ExportTab(export_tab, self)

        # 全モデル変数への一括トレース: Spinbox手入力・Entry入力をリアルタイムに反映する。
        # command= コールバックはSpinboxのボタン操作時しか発火しないため、
        # 変数自体の書き換えを監視することで手入力も拾う。
        for var_name in self.model.savable_vars:
            var = getattr(self.model, var_name)
            if isinstance(var, tk.Variable):
                var.trace_add("write", self.schedule_update)

        plot_panel = ttk.Frame(main_pane)
        main_pane.add(plot_panel, stretch="always")
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_panel)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.toolbar = NavigationToolbar2Tk(self.canvas, plot_panel)
        self.toolbar.update()

        # ドラッグ＆ドロップの登録
        self.file_listbox.drop_target_register(DND_FILES)
        self.file_listbox.dnd_bind("<<Drop>>", self.file_handler.on_drop_files)
        # グラフ領域へのドロップも許可
        self.canvas.get_tk_widget().drop_target_register(DND_FILES)
        self.canvas.get_tk_widget().dnd_bind(
            "<<Drop>>", self.file_handler.on_drop_files
        )

        self._toggle_spacing_widget()
        self._toggle_minor_xticks_widgets()
        self.plot_handler.update_plot()

    def _toggle_spacing_widget(self, *args):
        if self.model.stack_plots_var.get():
            self.spacing_label.grid()
            self.spacing_entry.grid()
        else:
            self.spacing_label.grid_remove()
            self.spacing_entry.grid_remove()
        self.schedule_update()

    def _toggle_minor_xticks_widgets(self, *args):
        if self.model.show_minor_xticks_var.get():
            self.xminor_tick_spacing_label.grid()
            self.xminor_tick_spacing_entry.grid()
        else:
            self.xminor_tick_spacing_label.grid_remove()
            self.xminor_tick_spacing_entry.grid_remove()
        self.schedule_update()

    def schedule_update(self, *args):
        if self._debounce_job:
            self.master.after_cancel(self._debounce_job)
        self._debounce_job = self.master.after(250, self.plot_handler.update_plot)

    def _validate_float(self, P):
        if P == "" or P == "-":
            return True
        try:
            # 部分的な指数表記を許可する。
            if (
                P.lower().endswith("e")
                or P.lower().endswith("e-")
                or P.lower().endswith("e+")
            ):
                return True
            float(P)
            return True
        except ValueError:
            self.bell()
            return False

    def on_closing(self):
        self.settings_handler.save_app_config()
        self.master.destroy()
