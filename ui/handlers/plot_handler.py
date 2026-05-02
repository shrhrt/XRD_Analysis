import os
import tkinter as tk
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from core import data_analyzer


class PlotHandler:
    """プロットの描画やエクスポート機能を管理するハンドラクラス"""

    def __init__(self, app, model):
        self.app = app
        self.model = model

    def get_current_plot_settings(self):
        # エラー状態(invalid)をリセットする。
        self.app.xmin_entry.state(["!invalid"])
        self.app.xmax_entry.state(["!invalid"])
        self.app.threshold_entry.state(["!invalid"])

        filepaths = self.app.file_listbox.get(0, tk.END)
        plot_data_full = [
            {
                "label": self.app.file_data[fp],
                "angles": self.app.parsed_data[fp][0],
                "intensities": self.app.parsed_data[fp][1],
            }
            for fp in filepaths
            if fp in self.app.file_data and fp in self.app.parsed_data
        ]

        try:
            threshold = (
                float(self.model.threshold_var.get())
                if self.model.threshold_var.get()
                else 0.0
            )
            spacing = self.model.plot_spacing_var.get()
            xmin = (
                float(self.model.xmin_var.get()) if self.model.xmin_var.get() else None
            )
            xmax = (
                float(self.model.xmax_var.get()) if self.model.xmax_var.get() else None
            )

            # xminとxmaxの論理エラーをチェックする。
            if xmin is not None and xmax is not None and xmin >= xmax:
                self.app.xmin_entry.state(["invalid"])  # エラー状態にする
                self.app.xmax_entry.state(["invalid"])
                return None  # Prevent plot update, no messagebox

        except ValueError:
            return None

        reference_peaks = [
            {
                "name": self.model.peak_name_vars[i].get().strip(),
                "angle": float(self.model.peak_angle_vars[i].get().strip()),
                "visible": self.model.peak_visible_vars[i].get(),
                "color": self.model.peak_color_vars[i].get(),
                "linestyle": self.model.peak_style_vars[i].get(),
            }
            for i in range(10)
            if self.model.peak_angle_vars[i].get().strip()
        ]

        appearance_settings = {
            "xlabel": self.model.xlabel_var.get(),
            "ylabel": self.model.ylabel_var.get(),
            "axis_label_fontsize": self.model.axis_label_fontsize_var.get(),
            "tick_label_fontsize": self.model.tick_label_fontsize_var.get(),
            "legend_fontsize": self.model.legend_fontsize_var.get(),
            "linewidth": self.model.plot_linewidth_var.get(),
            "tick_direction": self.model.tick_direction_var.get(),
            "threshold_handling": self.model.threshold_handling_var.get(),
            "xaxis_major_tick_spacing": self.model.xaxis_major_tick_spacing_var.get(),
            "show_grid": self.model.show_grid_var.get(),
            "ytop_padding_factor": self.model.ytop_padding_factor_var.get(),
            "hide_major_xtick_labels": self.model.hide_major_xtick_labels_var.get(),
            "show_minor_xticks": self.model.show_minor_xticks_var.get(),
            "xminor_tick_spacing": self.model.xminor_tick_spacing_var.get(),
            "peak_label_fontsize": self.model.peak_label_fontsize_var.get(),
            "peak_label_offset": self.model.peak_label_offset_var.get(),
            "peak_label_y": self.model.peak_label_y_var.get(),
            "match_math_font": self.model.match_math_font_var.get(),
            "legend_loc": self.model.legend_loc_var.get(),
            "legend_frame": self.model.legend_frame_var.get(),
            "legend_bgcolor": self.model.legend_bgcolor_var.get(),
            "legend_italic": self.model.legend_italic_var.get(),
            "yscale": self.model.yscale_var.get(),
            "font_family": self.model.font_family_var.get(),
        }

        peak_detection_settings = {
            "enabled": self.model.peak_detection_enabled_var.get(),
            "min_height": self.model.peak_detection_height_var.get(),
            "min_prominence": self.model.peak_detection_prominence_var.get(),
            "min_width": self.model.peak_detection_width_var.get(),
        }

        plot_settings = data_analyzer.PlotSettings(
            threshold=threshold,
            x_range=(xmin, xmax),
            reference_peaks=reference_peaks,
            show_legend=self.model.show_legend_var.get(),
            stack=self.model.stack_plots_var.get(),
            spacing=spacing,
            appearance=appearance_settings,
            peak_detection_settings=peak_detection_settings,
        )

        return plot_data_full, plot_settings

    def update_plot(self):
        result = self.get_current_plot_settings()
        if not result:
            self.app.ax.clear()
            self.app.ax.text(
                0.5,
                0.5,
                "ファイルを選択するか、設定を確認してください",
                ha="center",
                va="center",
                transform=self.app.ax.transAxes,
            )
            self.app.canvas.draw()
            return

        plot_data_full, settings = result

        if not plot_data_full:
            self.app.ax.clear()
            self.app.ax.text(
                0.5,
                0.5,
                "ファイルを選択してください",
                ha="center",
                va="center",
                transform=self.app.ax.transAxes,
            )
            self.app.canvas.draw()
            return

        match_math_font = settings.appearance.get("match_math_font", False)
        rc_params = {"mathtext.default": "regular"} if match_math_font else {}

        with plt.rc_context(rc_params):
            self.app.ax.clear()
            error_message = data_analyzer.draw_plot(
                ax=self.app.ax, plot_data_full=plot_data_full, settings=settings
            )
            if error_message:
                messagebox.showinfo("情報", error_message, parent=self.app.master)
            self.app.fig.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.15)
            self.app.canvas.draw()

    def get_legend_pos(self):
        leg = self.app.ax.get_legend()
        if leg and leg.get_visible():
            try:
                bbox = leg.get_window_extent()
                bbox_axes = bbox.transformed(self.app.ax.transAxes.inverted())
                return (bbox_axes.x0, bbox_axes.y0)
            except Exception:
                pass
        return None

    def preview_figure(self):
        result = self.get_current_plot_settings()
        if not result or not result[0]:
            messagebox.showwarning(
                "警告", "プレビュー対象のデータがありません。", parent=self.app.master
            )
            return

        plot_data_full, settings = result
        settings.legend_position = self.get_legend_pos()

        try:
            width = float(self.model.export_width_var.get())
            height = float(self.model.export_height_var.get())
            if width <= 0 or height <= 0:
                raise ValueError("サイズは正の値である必要があります。")
        except ValueError:
            messagebox.showerror(
                "エラー", "幅または高さの値が不正です。", parent=self.app.master
            )
            return

        preview_window = tk.Toplevel(self.app.master)
        preview_window.title("エクスポートプレビュー")

        # 予測可能性のためプレビューには固定DPIを使用する。
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

        # フィギュアサイズとツールバーに基づいてウィンドウサイズを設定する。
        preview_window.update_idletasks()
        width_px = int(width * preview_dpi)
        height_px = int(height * preview_dpi) + toolbar.winfo_height()
        preview_window.geometry(f"{width_px}x{height_px}")

    def save_figure(self):
        result = self.get_current_plot_settings()
        if not result or not result[0]:
            messagebox.showwarning(
                "警告", "保存対象のデータがありません。", parent=self.app.master
            )
            return

        plot_data_full, settings = result
        settings.legend_position = self.get_legend_pos()

        try:
            width = float(self.model.export_width_var.get())
            height = float(self.model.export_height_var.get())
            if width <= 0 or height <= 0:
                raise ValueError("サイズは正の値である必要があります。")
        except ValueError:
            messagebox.showerror(
                "エラー", "幅または高さの値が不正です。", parent=self.app.master
            )
            return

        default_filename = ""
        if self.app.file_listbox.size() > 0:
            first_filepath = self.app.file_listbox.get(0)
            legend_name = self.app.file_data.get(first_filepath, "")
            default_filename = os.path.splitext(legend_name)[0]

        filepath = filedialog.asksaveasfilename(
            title="グラフを保存",
            initialfile=default_filename,
            defaultextension=f".{self.model.export_format_var.get()}",
            filetypes=[
                (
                    f"{self.model.export_format_var.get().upper()} files",
                    f"*.{self.model.export_format_var.get()}",
                ),
                ("All files", "*.*"),
            ],
            parent=self.app.master,
        )
        if not filepath:
            return

        # 画像保存には高いDPIを使用する。
        save_dpi = 300
        fig = Figure(figsize=(width, height), dpi=save_dpi)
        ax = fig.add_subplot(111)

        match_math_font = settings.appearance.get("match_math_font", False)
        rc_params = {"mathtext.default": "regular"} if match_math_font else {}

        with plt.rc_context(rc_params):
            data_analyzer.draw_plot(
                ax=ax, plot_data_full=plot_data_full, settings=settings
            )
            # 新しいフィギュアに合わせてサブプロットのパラメータを調整する。
            fig.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.1)

            try:
                # ラベルが途切れないように bbox_inches='tight' を使用する。
                fig.savefig(
                    filepath, dpi=save_dpi, bbox_inches="tight", transparent=True
                )
                messagebox.showinfo(
                    "成功", f"グラフを保存しました:\n{filepath}", parent=self.app.master
                )
            except Exception as e:
                messagebox.showerror(
                    "エラー",
                    f"ファイルの保存中にエラーが発生しました:\n{e}",
                    parent=self.app.master,
                )

    def toggle_legend_visibility(self):
        if self.app.ax:
            legend = self.app.ax.get_legend()
            if legend:
                legend.set_visible(self.model.show_legend_var.get())
                self.app.canvas.draw_idle()
