import math
import tkinter as tk
from tkinter import ttk


class FitTab:
    """ピークフィットタブのUIと結果テーブルを管理するクラス"""

    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self._rows = []  # (result_dict, treeview_iid) のリスト
        self.build()

    def build(self):
        self.parent.columnconfigure(0, weight=1)
        self.parent.rowconfigure(1, weight=1)

        # --- 上部: モード切替 ---
        top = ttk.Frame(self.parent, padding=(5, 5, 5, 0))
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)

        self._mode_btn = ttk.Button(
            top, text="フィットモード: OFF", command=self._toggle_mode, width=22
        )
        self._mode_btn.grid(row=0, column=0, padx=(0, 8))
        ttk.Label(top, text="グラフ上をドラッグしてピーク範囲を選択").grid(
            row=0, column=1, sticky="w"
        )

        # --- 結果テーブル ---
        tree_frame = ttk.Frame(self.parent)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        cols = ("center", "fwhm", "d", "D", "r2")
        self._tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings", selectmode="browse", height=8
        )
        self._tree.heading("center", text="2θ (°)")
        self._tree.heading("fwhm", text="FWHM (°)")
        self._tree.heading("d", text="d (Å)")
        self._tree.heading("D", text="D (Å)")
        self._tree.heading("r2", text="R²")
        self._tree.column("center", width=115, anchor="center", minwidth=80)
        self._tree.column("fwhm", width=115, anchor="center", minwidth=80)
        self._tree.column("d", width=72, anchor="center", minwidth=55)
        self._tree.column("D", width=105, anchor="center", minwidth=70)
        self._tree.column("r2", width=58, anchor="center", minwidth=45)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        # --- 下部: ボタン ---
        btn_frame = ttk.Frame(self.parent, padding=(5, 0, 5, 4))
        btn_frame.grid(row=2, column=0, sticky="ew")
        ttk.Button(btn_frame, text="選択行を削除", command=self._delete_selected).pack(
            side="left", padx=(0, 4)
        )
        ttk.Button(btn_frame, text="全クリア", command=self._clear_all).pack(
            side="left", padx=(0, 4)
        )
        ttk.Button(
            btn_frame, text="クリップボードにコピー", command=self._copy_to_clipboard
        ).pack(side="left")

        # --- エラー表示 ---
        self._error_var = tk.StringVar()
        ttk.Label(
            self.parent,
            textvariable=self._error_var,
            foreground="red",
            wraplength=320,
        ).grid(row=3, column=0, sticky="w", padx=5, pady=(0, 4))

        # --- 説明 ---
        note = (
            "D (Å): シェラー式による結晶子サイズ (K=0.94, λ=1.78897 Å)\n"
            "±: フィットパラメータの標準誤差"
        )
        ttk.Label(self.parent, text=note, foreground="gray", font=("", 8)).grid(
            row=4, column=0, sticky="w", padx=5, pady=(0, 4)
        )

    # ------------------------------------------------------------------ #
    def _toggle_mode(self):
        if self.app.fit_handler.mode_active:
            self.app.fit_handler.disable_mode()
            self._mode_btn.config(text="フィットモード: OFF")
        else:
            self.app.fit_handler.enable_mode()
            self._mode_btn.config(text="フィットモード: ON ")

    def add_result(self, result):
        def _fmt(val, err=None, dec=3):
            if not math.isfinite(val):
                return "N/A"
            s = f"{val:.{dec}f}"
            if err is not None and math.isfinite(err):
                s += f" ±{err:.{dec}f}"
            return s

        row = (
            _fmt(result["center"], result["center_err"], 3),
            _fmt(result["fwhm"], result["fwhm_err"], 3),
            f"{result['d_spacing']:.4f}",
            _fmt(result["crystallite_size"], result["crystallite_size_err"], 1),
            f"{result['r_squared']:.4f}",
        )
        iid = self._tree.insert("", "end", values=row)
        self._rows.append((result, iid))
        self._tree.see(iid)

    def show_error(self, msg):
        self._error_var.set(f"エラー: {msg}")

    def clear_error(self):
        self._error_var.set("")

    # ------------------------------------------------------------------ #
    def _delete_selected(self):
        sel = self._tree.selection()
        if not sel:
            return
        iid = sel[0]
        index = next(
            (i for i, (_, r_iid) in enumerate(self._rows) if r_iid == iid), None
        )
        if index is None:
            return
        self._tree.delete(iid)
        self._rows.pop(index)
        self.app.fit_handler.remove_at(index)
        self.app.plot_handler.update_plot()

    def _clear_all(self):
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._rows.clear()
        self.app.fit_handler.clear_results()
        self.app.plot_handler.update_plot()

    def _copy_to_clipboard(self):
        header = "2θ (°)\tFWHM (°)\td (Å)\tD (Å)\tR²"
        rows = [
            "\t".join(self._tree.item(item, "values"))
            for item in self._tree.get_children()
        ]
        self.app.master.clipboard_clear()
        self.app.master.clipboard_append(header + "\n" + "\n".join(rows))
