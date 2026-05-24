import os
from core import data_analyzer

_FIT_COLORS = ["#00e676", "#00e5ff", "#ff6d00", "#d500f9", "#ffea00", "#ff4081"]


class FitHandler:
    """グラフ上のドラッグ操作でピークフィットを実行するハンドラ"""

    def __init__(self, app, model):
        self.app = app
        self.model = model
        self._press_x = None
        self._span = None
        self._cids = []
        self.fit_results = []
        self.mode_active = False
        self._color_idx = 0

    def enable_mode(self):
        if self.mode_active:
            return
        self.mode_active = True
        self._cids = [
            self.app.canvas.mpl_connect("button_press_event", self._on_press),
            self.app.canvas.mpl_connect("motion_notify_event", self._on_motion),
            self.app.canvas.mpl_connect("button_release_event", self._on_release),
        ]

    def disable_mode(self):
        if not self.mode_active:
            return
        self.mode_active = False
        for cid in self._cids:
            self.app.canvas.mpl_disconnect(cid)
        self._cids = []
        self._press_x = None
        if self._span is not None:
            try:
                self._span.remove()
            except Exception:
                pass
            self._span = None
            self.app.canvas.draw_idle()

    def _toolbar_active(self):
        toolbar = getattr(self.app, "toolbar", None)
        return toolbar is not None and str(toolbar.mode) != ""

    def _on_press(self, event):
        if event.inaxes != self.app.ax or event.button != 1:
            return
        if self._toolbar_active():
            return
        self._press_x = event.xdata

    def _on_motion(self, event):
        if self._press_x is None or event.inaxes != self.app.ax or event.xdata is None:
            return
        if self._span is not None:
            try:
                self._span.remove()
            except Exception:
                pass
        self._span = self.app.ax.axvspan(
            self._press_x, event.xdata, alpha=0.15, color="green"
        )
        self.app.canvas.draw_idle()

    def _on_release(self, event):
        if self._press_x is None or event.button != 1:
            self._press_x = None
            return

        if self._span is not None:
            try:
                self._span.remove()
            except Exception:
                pass
            self._span = None

        if event.inaxes != self.app.ax or event.xdata is None:
            self._press_x = None
            self.app.canvas.draw_idle()
            return

        x0, x1 = sorted([self._press_x, event.xdata])
        self._press_x = None

        if abs(x1 - x0) < 0.05:
            self.app.canvas.draw_idle()
            return

        # 選択中ファイルのデータを取得
        sel = self.app.file_listbox.curselection()
        if sel:
            fp = self.app.file_listbox.get(sel[0])
        elif self.app.file_listbox.size() > 0:
            fp = self.app.file_listbox.get(0)
        else:
            self.app.canvas.draw_idle()
            return

        if fp not in self.app.parsed_data:
            self.app.canvas.draw_idle()
            return

        angles, intensities = self.app.parsed_data[fp]

        try:
            result = data_analyzer.fit_peak_gaussian(angles, intensities, x0, x1)
        except Exception as e:
            self.app.fit_tab.show_error(str(e))
            self.app.canvas.draw_idle()
            return

        color = _FIT_COLORS[self._color_idx % len(_FIT_COLORS)]
        self._color_idx += 1

        self.app.ax.plot(
            result["x_fit"],
            result["y_fit"],
            color=color,
            linewidth=1.5,
            linestyle="--",
            zorder=5,
        )

        result["color"] = color
        result["file"] = os.path.basename(fp)
        result["legend"] = self.app.file_data.get(fp, os.path.basename(fp))
        self.fit_results.append(result)
        self.app.fit_tab.add_result(result)
        self.app.fit_tab.clear_error()
        self.app.canvas.draw_idle()

    def redraw_fits(self):
        """update_plot による ax.clear() 後にフィット曲線を再描画する。
        canvas.draw() は呼び出し元（plot_handler）に任せる。"""
        for result in self.fit_results:
            self.app.ax.plot(
                result["x_fit"],
                result["y_fit"],
                color=result["color"],
                linewidth=1.5,
                linestyle="--",
                zorder=5,
            )

    def remove_at(self, index):
        if 0 <= index < len(self.fit_results):
            self.fit_results.pop(index)

    def clear_results(self):
        self.fit_results.clear()
        self._color_idx = 0
