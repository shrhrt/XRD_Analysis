import tkinter as tk
import os
from tkinter import ttk, filedialog, messagebox
import numpy as np
import math
from matplotlib.figure import Figure

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
import data_analyzer
from config_manager import ConfigManager
import sv_ttk
from ui.tab_plot import PlotSettingsTab
from ui.tab_reference import ReferencePeaksTab
from ui.tab_analysis import AnalysisTab
from ui.tab_appearance import AppearanceTab
from ui.tab_export import ExportTab


class XRDPlotter(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("XRD Data Plotter")
        self.master.geometry("1280x720")
        self.pack(fill=tk.BOTH, expand=True)

        (
            self.peak_name_vars,
            self.peak_angle_vars,
            self.peak_visible_vars,
            self.peak_color_vars,
            self.peak_style_vars,
            self.peak_color_buttons,
        ) = [], [], [], [], [], []
        self.xmin_var, self.xmax_var = (
            tk.StringVar(value="30"),
            tk.StringVar(value="130"),
        )
        self.threshold_var, self.legend_name_var = (
            tk.StringVar(value="1"),
            tk.StringVar(),
        )
        self.show_legend_var, self.stack_plots_var = (
            tk.BooleanVar(value=True),
            tk.BooleanVar(value=False),
        )
        self.legend_loc_var = tk.StringVar(value="best")
        self.legend_frame_var = tk.BooleanVar(value=True)
        self.legend_bgcolor_var = tk.StringVar(value="white")
        self.legend_italic_var = tk.BooleanVar(value=False)
        self.threshold_handling_var = tk.StringVar(value="clip")  # "hide" or "clip"
        self.yscale_var = tk.StringVar(value="log")
        self.font_family_var = tk.StringVar(value="sans-serif")
        self.plot_spacing_var = tk.DoubleVar(value=3)
        self.xlabel_var, self.ylabel_var = (
            tk.StringVar(value="2θ/ω (degree)"),
            tk.StringVar(value="Log Intensity (arb. Units)"),
        )
        self.axis_label_fontsize_var, self.tick_label_fontsize_var = (
            tk.DoubleVar(value=20),
            tk.DoubleVar(value=16),
        )
        self.legend_fontsize_var, self.plot_linewidth_var = (
            tk.DoubleVar(value=10),
            tk.DoubleVar(value=1.0),
        )
        self.tick_direction_var = tk.StringVar(value="in")
        self.xaxis_major_tick_spacing_var, self.show_grid_var = (
            tk.DoubleVar(value=5),
            tk.BooleanVar(value=False),
        )
        self.ytop_padding_factor_var = tk.DoubleVar(value=1.5)
        self.hide_major_xtick_labels_var, self.show_minor_xticks_var = (
            tk.BooleanVar(value=False),
            tk.BooleanVar(value=True),
        )
        self.xminor_tick_spacing_var = tk.DoubleVar(value=1.0)
        self.peak_label_fontsize_var = tk.DoubleVar(value=9)
        self.peak_label_offset_var = tk.DoubleVar(value=0.4)
        self.peak_label_y_var = tk.DoubleVar(value=0.90)
        self.match_math_font_var = tk.BooleanVar(value=False)
        self.d_spacing_input_2theta_var, self.d_spacing_result_var = (
            tk.StringVar(),
            tk.StringVar(value="d-spacing (Å)"),
        )
        self.lc_input_d_var, self.lc_h_var, self.lc_k_var, self.lc_l_var = (
            tk.StringVar(),
            tk.StringVar(value="1"),
            tk.StringVar(value="0"),
            tk.StringVar(value="0"),
        )
        self.lc_result_var = tk.StringVar(value="a = ?")
        self.export_width_var, self.export_height_var, self.export_format_var = (
            tk.StringVar(value="6"),
            tk.StringVar(value="6"),
            tk.StringVar(value="png"),
        )
        self.selected_substance_var = tk.StringVar()

        # List of tk variables to be saved/loaded
        self._savable_vars = [
            "xmin_var",
            "xmax_var",
            "threshold_var",
            "show_legend_var",
            "stack_plots_var",
            "threshold_handling_var",
            "plot_spacing_var",
            "xlabel_var",
            "ylabel_var",
            "legend_loc_var",
            "legend_frame_var",
            "legend_bgcolor_var",
            "legend_italic_var",
            "yscale_var",
            "font_family_var",
            "axis_label_fontsize_var",
            "tick_label_fontsize_var",
            "legend_fontsize_var",
            "plot_linewidth_var",
            "tick_direction_var",
            "xaxis_major_tick_spacing_var",
            "show_grid_var",
            "ytop_padding_factor_var",
            "hide_major_xtick_labels_var",
            "show_minor_xticks_var",
            "xminor_tick_spacing_var",
            "peak_label_fontsize_var",
            "peak_label_offset_var",
            "peak_label_y_var",
            "match_math_font_var",
            "d_spacing_input_2theta_var",
            "lc_input_d_var",
            "lc_h_var",
            "lc_k_var",
            "lc_l_var",
            "export_width_var",
            "export_height_var",
            "export_format_var",
            "peak_detection_enabled_var",
            "peak_detection_height_var",
            "peak_detection_prominence_var",
            "peak_detection_width_var",
        ]

        # Analysis settings
        self.peak_detection_enabled_var = tk.BooleanVar(value=False)
        self.peak_detection_height_var = tk.DoubleVar(value=10)
        self.peak_detection_prominence_var = tk.DoubleVar(value=10)
        self.peak_detection_width_var = tk.DoubleVar(value=1.0)

        self.recent_files = []
        # ユーザーのホームディレクトリ(C:\Users\ユーザー名\)の下に専用フォルダを作成
        config_dir = os.path.join(os.path.expanduser("~"), ".xrd_plotter")
        os.makedirs(config_dir, exist_ok=True)
        self.config_file = os.path.join(config_dir, "xrd_app_config.json")
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self._debounce_job, self.file_data, self.parsed_data = None, {}, {}

        # Register validation command
        self.vcmd_float = (self.register(self._validate_float), "%P")

        self.fig = Figure(figsize=(6, 4))
        self.ax = self.fig.add_subplot(111)

        self.create_menu()
        self.create_widgets()
        self.load_app_config()

    def toggle_theme(self):
        if sv_ttk.get_theme() == "dark":
            sv_ttk.set_theme("light")
            self.theme_button.config(text="ダークモードに切り替え")
        else:
            sv_ttk.set_theme("dark")
            self.theme_button.config(text="ライトモードに切り替え")

    def create_menu(self):
        self.menubar = tk.Menu(self.master)
        self.master.config(menu=self.menubar)

        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="ファイル", menu=file_menu)

        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="最近開いたファイル", menu=self.recent_menu)
        self.update_recent_menu()
        file_menu.add_separator()
        file_menu.add_command(label="設定を読み込む...", command=self.load_settings)
        file_menu.add_command(label="設定を保存...", command=self.save_settings)
        file_menu.add_separator()
        file_menu.add_command(
            label="グラフを画像として保存...", command=self.save_figure
        )
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.on_closing)

    def create_widgets(self):
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        self.theme_button = ttk.Button(
            top_frame, text="ダークモードに切り替え", command=self.toggle_theme
        )
        self.theme_button.pack(side=tk.RIGHT)

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
            export_tab,
        ) = (
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
        notebook.add(export_tab, text="エクスポート")

        PlotSettingsTab(plot_settings_tab, self)
        ReferencePeaksTab(reference_peaks_tab, self)
        AppearanceTab(appearance_tab, self)
        AnalysisTab(analysis_tab, self)
        ExportTab(export_tab, self)

        plot_panel = ttk.Frame(main_pane)
        main_pane.add(plot_panel, stretch="always")
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_panel)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(self.canvas, plot_panel)
        toolbar.update()

        self._toggle_spacing_widget()
        self._toggle_minor_xticks_widgets()
        self.update_plot()

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

    def _get_current_plot_settings(self):
        # エラー状態(invalid)をリセット
        self.xmin_entry.state(["!invalid"])
        self.xmax_entry.state(["!invalid"])
        self.threshold_entry.state(["!invalid"])

        filepaths = self.file_listbox.get(0, tk.END)
        plot_data_full = [
            {
                "label": self.file_data[fp],
                "angles": self.parsed_data[fp][0],
                "intensities": self.parsed_data[fp][1],
            }
            for fp in filepaths
            if fp in self.file_data and fp in self.parsed_data
        ]

        try:
            threshold = (
                float(self.threshold_var.get()) if self.threshold_var.get() else 0.0
            )
            spacing = self.plot_spacing_var.get()
            xmin = float(self.xmin_var.get()) if self.xmin_var.get() else None
            xmax = float(self.xmax_var.get()) if self.xmax_var.get() else None

            # Check for logical error between xmin and xmax
            if xmin is not None and xmax is not None and xmin >= xmax:
                self.xmin_entry.state(["invalid"])  # エラー状態にする
                self.xmax_entry.state(["invalid"])
                return None  # Prevent plot update, no messagebox

        except ValueError:
            # This catches intermediate valid-while-typing states like "-", "1.e-", etc.
            # or if validation was somehow bypassed.
            # Just fail silently, the plot will update when input is valid.
            return None

        reference_peaks = [
            {
                "name": self.peak_name_vars[i].get().strip(),
                "angle": float(self.peak_angle_vars[i].get().strip()),
                "visible": self.peak_visible_vars[i].get(),
                "color": self.peak_color_vars[i].get(),
                "linestyle": self.peak_style_vars[i].get(),
            }
            for i in range(10)
            if self.peak_angle_vars[i].get().strip()
        ]

        appearance_settings = {
            "xlabel": self.xlabel_var.get(),
            "ylabel": self.ylabel_var.get(),
            "axis_label_fontsize": self.axis_label_fontsize_var.get(),
            "tick_label_fontsize": self.tick_label_fontsize_var.get(),
            "legend_fontsize": self.legend_fontsize_var.get(),
            "linewidth": self.plot_linewidth_var.get(),
            "tick_direction": self.tick_direction_var.get(),
            "threshold_handling": self.threshold_handling_var.get(),
            "xaxis_major_tick_spacing": self.xaxis_major_tick_spacing_var.get(),
            "show_grid": self.show_grid_var.get(),
            "ytop_padding_factor": self.ytop_padding_factor_var.get(),
            "hide_major_xtick_labels": self.hide_major_xtick_labels_var.get(),
            "show_minor_xticks": self.show_minor_xticks_var.get(),
            "xminor_tick_spacing": self.xminor_tick_spacing_var.get(),
            "peak_label_fontsize": self.peak_label_fontsize_var.get(),
            "peak_label_offset": self.peak_label_offset_var.get(),
            "peak_label_y": self.peak_label_y_var.get(),
            "match_math_font": self.match_math_font_var.get(),
            "legend_loc": self.legend_loc_var.get(),
            "legend_frame": self.legend_frame_var.get(),
            "legend_bgcolor": self.legend_bgcolor_var.get(),
            "legend_italic": self.legend_italic_var.get(),
            "yscale": self.yscale_var.get(),
            "font_family": self.font_family_var.get(),
        }

        peak_detection_settings = {
            "enabled": self.peak_detection_enabled_var.get(),
            "min_height": self.peak_detection_height_var.get(),
            "min_prominence": self.peak_detection_prominence_var.get(),
            "min_width": self.peak_detection_width_var.get(),
        }

        plot_settings = data_analyzer.PlotSettings(
            threshold=threshold,
            x_range=(xmin, xmax),
            reference_peaks=reference_peaks,
            show_legend=self.show_legend_var.get(),
            stack=self.stack_plots_var.get(),
            spacing=spacing,
            appearance=appearance_settings,
            peak_detection_settings=peak_detection_settings,
        )

        return plot_data_full, plot_settings

    def update_plot(self):
        result = self._get_current_plot_settings()
        if not result:
            self.ax.clear()
            self.ax.text(
                0.5,
                0.5,
                "ファイルを選択するか、設定を確認してください",
                ha="center",
                va="center",
                transform=self.ax.transAxes,
            )
            self.canvas.draw()
            return

        plot_data_full, settings = result

        if not plot_data_full:
            self.ax.clear()
            self.ax.text(
                0.5,
                0.5,
                "ファイルを選択してください",
                ha="center",
                va="center",
                transform=self.ax.transAxes,
            )
            self.canvas.draw()
            return

        match_math_font = settings.appearance.get("match_math_font", False)
        rc_params = {"mathtext.default": "regular"} if match_math_font else {}

        with plt.rc_context(rc_params):
            self.ax.clear()
            error_message = data_analyzer.draw_plot(
                ax=self.ax, plot_data_full=plot_data_full, settings=settings
            )
            if error_message:
                messagebox.showinfo("情報", error_message)
            self.fig.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.15)
            self.canvas.draw()

    def add_to_recent(self, filepath):
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)
        self.recent_files.insert(0, filepath)
        if len(self.recent_files) > 10:
            self.recent_files = self.recent_files[:10]
        self.update_recent_menu()

    def update_recent_menu(self):
        self.recent_menu.delete(0, tk.END)
        if not self.recent_files:
            self.recent_menu.add_command(label="(履歴なし)", state="disabled")
        else:
            for fp in self.recent_files:
                display_name = fp if len(fp) < 60 else "..." + fp[-57:]
                self.recent_menu.add_command(
                    label=display_name, command=lambda f=fp: self.open_recent_file(f)
                )
            self.recent_menu.add_separator()
            self.recent_menu.add_command(
                label="履歴をクリア", command=self.clear_recent_files
            )

    def clear_recent_files(self):
        self.recent_files = []
        self.update_recent_menu()

    def open_recent_file(self, filepath):
        if not os.path.exists(filepath):
            messagebox.showerror(
                "エラー", f"ファイルが見つかりません:\n{filepath}", parent=self.master
            )
            if filepath in self.recent_files:
                self.recent_files.remove(filepath)
                self.update_recent_menu()
            return
        if filepath not in self.file_data:
            angles, intensities = data_analyzer.parse_ras_file(filepath)
            if angles is None or intensities is None:
                messagebox.showwarning(
                    "警告",
                    f"ファイル {os.path.basename(filepath)} の読み込みに失敗しました。",
                    parent=self.master,
                )
                return
            self.parsed_data[filepath] = (angles, intensities)
            self.file_data[filepath] = os.path.basename(filepath)
            self.file_listbox.insert(tk.END, filepath)
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(tk.END)
            self.on_file_select(None)
            self.schedule_update()
        self.add_to_recent(filepath)

    def select_files(self):
        filepaths = filedialog.askopenfilenames(
            title="XRDファイルを選択",
            filetypes=[("RAS files", "*.ras"), ("All files", "*.*")],
        )
        if filepaths:
            for fp in filepaths:
                if fp not in self.file_data:
                    angles, intensities = data_analyzer.parse_ras_file(fp)
                    if angles is None or intensities is None:
                        messagebox.showwarning(
                            "警告",
                            f"ファイル {os.path.basename(fp)} の読み込みに失敗しました。",
                        )
                        continue
                    self.parsed_data[fp] = (angles, intensities)
                    self.file_data[fp] = os.path.basename(fp)
                    self.file_listbox.insert(tk.END, fp)
                    self.add_to_recent(fp)
            if not self.file_listbox.curselection():
                self.file_listbox.selection_set(tk.END)
                self.on_file_select(None)
            self.schedule_update()

    def remove_selected_file(self):
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            return
        selected_filepath = self.file_listbox.get(selected_indices[0])
        if selected_filepath in self.file_data:
            del self.file_data[selected_filepath]
        if selected_filepath in self.parsed_data:
            del self.parsed_data[selected_filepath]
        self.file_listbox.delete(selected_indices[0])
        self.legend_name_entry.config(state="disabled")
        self.legend_name_var.set("")
        if self.file_listbox.size() > 0:
            new_selection_index = min(selected_indices[0], self.file_listbox.size() - 1)
            self.file_listbox.selection_set(new_selection_index)
            self.on_file_select(None)
        self.schedule_update()

    def move_file_up(self):
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            return
        idx = selected_indices[0]
        if idx > 0:
            filepath = self.file_listbox.get(idx)
            self.file_listbox.delete(idx)
            self.file_listbox.insert(idx - 1, filepath)
            self.file_listbox.selection_set(idx - 1)
            self.schedule_update()

    def move_file_down(self):
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            return
        idx = selected_indices[0]
        if idx < self.file_listbox.size() - 1:
            filepath = self.file_listbox.get(idx)
            self.file_listbox.delete(idx)
            self.file_listbox.insert(idx + 1, filepath)
            self.file_listbox.selection_set(idx + 1)
            self.schedule_update()

    def _get_legend_pos(self):
        leg = self.ax.get_legend()
        if leg and leg.get_visible():
            try:
                bbox = leg.get_window_extent()
                bbox_axes = bbox.transformed(self.ax.transAxes.inverted())
                return (bbox_axes.x0, bbox_axes.y0)
            except Exception:
                pass
        return None

    def preview_figure(self):
        result = self._get_current_plot_settings()
        if not result or not result[0]:
            messagebox.showwarning(
                "警告", "プレビュー対象のデータがありません。", parent=self.master
            )
            return

        plot_data_full, settings = result
        settings.legend_position = self._get_legend_pos()

        try:
            width = float(self.export_width_var.get())
            height = float(self.export_height_var.get())
            if width <= 0 or height <= 0:
                raise ValueError("サイズは正の値である必要があります。")
        except ValueError:
            messagebox.showerror(
                "エラー", "幅または高さの値が不正です。", parent=self.master
            )
            return

        preview_window = tk.Toplevel(self.master)
        preview_window.title("エクスポートプレビュー")

        # Use a fixed DPI for the preview for predictability
        preview_dpi = 100
        fig = Figure(figsize=(width, height), dpi=preview_dpi)
        ax = fig.add_subplot(111)

        match_math_font = settings.appearance.get("match_math_font", False)
        rc_params = {"mathtext.default": "regular"} if match_math_font else {}

        with plt.rc_context(rc_params):
            data_analyzer.draw_plot(
                ax=ax, plot_data_full=plot_data_full, settings=settings
            )
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
        result = self._get_current_plot_settings()
        if not result or not result[0]:
            messagebox.showwarning(
                "警告", "保存対象のデータがありません。", parent=self.master
            )
            return

        plot_data_full, settings = result
        settings.legend_position = self._get_legend_pos()

        try:
            width = float(self.export_width_var.get())
            height = float(self.export_height_var.get())
            if width <= 0 or height <= 0:
                raise ValueError("サイズは正の値である必要があります。")
        except ValueError:
            messagebox.showerror(
                "エラー", "幅または高さの値が不正です。", parent=self.master
            )
            return

        default_filename = ""
        if self.file_listbox.size() > 0:
            first_filepath = self.file_listbox.get(0)
            legend_name = self.file_data.get(first_filepath, "")
            default_filename = os.path.splitext(legend_name)[0]

        filepath = filedialog.asksaveasfilename(
            title="グラフを保存",
            initialfile=default_filename,
            defaultextension=f".{self.export_format_var.get()}",
            filetypes=[
                (
                    f"{self.export_format_var.get().upper()} files",
                    f"*.{self.export_format_var.get()}",
                ),
                ("All files", "*.*"),
            ],
            parent=self.master,
        )
        if not filepath:
            return

        # Use a high DPI for saving the figure
        save_dpi = 300
        fig = Figure(figsize=(width, height), dpi=save_dpi)
        ax = fig.add_subplot(111)

        match_math_font = settings.appearance.get("match_math_font", False)
        rc_params = {"mathtext.default": "regular"} if match_math_font else {}

        with plt.rc_context(rc_params):
            data_analyzer.draw_plot(
                ax=ax, plot_data_full=plot_data_full, settings=settings
            )
            # Adjust subplot parameters for the new figure
            fig.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.1)

            try:
                # Use bbox_inches='tight' to ensure labels are not cut off
                fig.savefig(
                    filepath, dpi=save_dpi, bbox_inches="tight", transparent=True
                )
                messagebox.showinfo(
                    "成功", f"グラフを保存しました:\n{filepath}", parent=self.master
                )
            except Exception as e:
                messagebox.showerror(
                    "エラー",
                    f"ファイルの保存中にエラーが発生しました:\n{e}",
                    parent=self.master,
                )

    def on_file_select(self, event):
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
        if self.ax:
            legend = self.ax.get_legend()
            if legend:
                legend.set_visible(self.show_legend_var.get())
                self.canvas.draw_idle()

    def schedule_update(self, *args):
        if self._debounce_job:
            self.master.after_cancel(self._debounce_job)
        self._debounce_job = self.master.after(250, self.update_plot)

    def _validate_float(self, P):
        if P == "" or P == "-":
            return True
        try:
            # Allow partial scientific notation
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

    def _build_config_dict(self, include_recent=False) -> dict:
        """現在のUIの入力状態から設定辞書を構築します。"""
        settings = {
            "files": {
                "filepaths": list(self.file_listbox.get(0, tk.END)),
                "file_data": self.file_data,
            },
            "variables": {
                var_name: getattr(self, var_name).get()
                for var_name in self._savable_vars
            },
            "reference_peaks": [
                {
                    "name": self.peak_name_vars[i].get(),
                    "angle": self.peak_angle_vars[i].get(),
                    "visible": self.peak_visible_vars[i].get(),
                    "color": self.peak_color_vars[i].get(),
                    "style": self.peak_style_vars[i].get(),
                }
                for i in range(len(self.peak_name_vars))
            ],
        }
        if include_recent:
            settings["recent_files"] = self.recent_files
        return settings

    def _apply_config_dict(self, settings: dict, is_app_config: bool = False):
        """設定辞書を読み込み、UIに反映させます。"""
        if is_app_config and "recent_files" in settings:
            self.recent_files = settings["recent_files"]
            self.update_recent_menu()

        if not is_app_config:
            self.file_listbox.delete(0, tk.END)
            self.file_data.clear()
            self.parsed_data.clear()
            self.legend_name_entry.config(state="disabled")
            self.legend_name_var.set("")

        loaded_filepaths = settings.get("files", {}).get("filepaths", [])
        loaded_file_data = settings.get("files", {}).get("file_data", {})

        for fp in loaded_filepaths:
            if os.path.exists(fp):
                angles, intensities = data_analyzer.parse_ras_file(fp)
                if angles is not None and intensities is not None:
                    self.parsed_data[fp] = (angles, intensities)
                    self.file_data[fp] = loaded_file_data.get(fp, os.path.basename(fp))
                    self.file_listbox.insert(tk.END, fp)
                elif not is_app_config:
                    messagebox.showwarning(
                        "警告",
                        f"ファイル {os.path.basename(fp)} の読み込みに失敗しました。スキップします。",
                        parent=self.master,
                    )
            elif not is_app_config:
                messagebox.showwarning(
                    "警告",
                    f"ファイルが見つかりません: {fp}\nこのファイルはスキップされました。",
                    parent=self.master,
                )

        if self.file_listbox.size() > 0:
            self.file_listbox.selection_set(0)
            self.on_file_select(None)

        if "variables" in settings:
            for var_name, value in settings["variables"].items():
                if hasattr(self, var_name):
                    try:
                        getattr(self, var_name).set(value)
                    except Exception:
                        pass
        elif "export_format" in settings:  # Backward compatibility
            if "export_format" in settings:
                self.export_format_var.set(settings["export_format"])
            if "export_width" in settings:
                self.export_width_var.set(settings["export_width"])
            if "export_height" in settings:
                self.export_height_var.set(settings["export_height"])

        if "reference_peaks" in settings:
            for i, peak_data in enumerate(settings["reference_peaks"]):
                if i < len(self.peak_name_vars):
                    self.peak_name_vars[i].set(peak_data.get("name", ""))
                    self.peak_angle_vars[i].set(peak_data.get("angle", ""))
                    self.peak_visible_vars[i].set(peak_data.get("visible", False))
                    color = peak_data.get("color", "#000000")
                    self.peak_color_vars[i].set(color)
                    self.peak_color_buttons[i].config(fg=color)
                    self.peak_style_vars[i].set(peak_data.get("style", "--"))

        self._toggle_spacing_widget()
        self._toggle_minor_xticks_widgets()
        self.schedule_update()

    def save_settings(self):
        """Saves current plot settings to a JSON file."""
        default_filename = ""
        if self.file_listbox.size() > 0:
            first_filepath = self.file_listbox.get(0)
            legend_name = self.file_data.get(first_filepath, "")
            default_filename = os.path.splitext(legend_name)[0]

        filepath = filedialog.asksaveasfilename(
            title="設定を保存",
            initialfile=default_filename,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            defaultextension=".json",
            parent=self.master,
        )
        if not filepath:
            return

        settings = self._build_config_dict()
        if ConfigManager.save_to_file(filepath, settings):
            messagebox.showinfo(
                "成功", f"設定を保存しました:\n{filepath}", parent=self.master
            )
        else:
            messagebox.showerror(
                "エラー", "設定の保存中にエラーが発生しました", parent=self.master
            )

    def load_settings(self):
        """Loads plot settings from a JSON file."""
        filepath = filedialog.askopenfilename(
            title="設定を読み込む",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            parent=self.master,
        )
        if not filepath:
            return

        settings = ConfigManager.load_from_file(filepath)
        if settings is None:
            messagebox.showerror(
                "エラー", "設定の読み込みに失敗しました", parent=self.master
            )
            return

        self._apply_config_dict(settings, is_app_config=False)
        messagebox.showinfo("成功", "設定を読み込みました。", parent=self.master)

    def load_app_config(self):
        settings = ConfigManager.load_from_file(self.config_file)
        if settings:
            self._apply_config_dict(settings, is_app_config=True)

    def save_app_config(self):
        settings = self._build_config_dict(include_recent=True)
        ConfigManager.save_to_file(self.config_file, settings)

    def on_closing(self):
        self.save_app_config()
        self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()

    # sv_ttkテーマを適用 ("light" または "dark" を選択可能)
    sv_ttk.set_theme("light")

    app = XRDPlotter(master=root)
    app.mainloop()
