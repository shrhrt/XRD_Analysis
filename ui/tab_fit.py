import math
import tkinter as tk
from tkinter import ttk


class FitTab:
    """ピークフィットタブ — ファイル選択・結果テーブル・格子定数計算を一画面に集約"""

    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self._rows = []  # list of (result_dict, treeview_iid)

        self._d_var = tk.StringVar()
        self._h_var = tk.StringVar(value="0")
        self._k_var = tk.StringVar(value="0")
        self._l_var = tk.StringVar(value="2")
        self._lc_result_var = tk.StringVar()
        self._error_var = tk.StringVar()

        self.build()

        for v in (self._d_var, self._h_var, self._k_var, self._l_var):
            v.trace_add("write", self._update_lattice)

    # ------------------------------------------------------------------ #
    def build(self):
        self.parent.columnconfigure(0, weight=1)
        self.parent.rowconfigure(2, weight=1)

        # --- ファイル選択 ---
        f0 = ttk.Frame(self.parent, padding=(5, 5, 5, 2))
        f0.grid(row=0, column=0, sticky="ew")
        f0.columnconfigure(1, weight=1)
        ttk.Label(f0, text="対象ファイル:").grid(row=0, column=0, sticky="w", padx=(0, 4))
        self._file_combo = ttk.Combobox(
            f0, state="readonly", postcommand=self._refresh_file_list
        )
        self._file_combo.grid(row=0, column=1, sticky="ew")
        self._file_combo.bind("<<ComboboxSelected>>", self._on_file_combo_select)

        # --- モード切替 ---
        f1 = ttk.Frame(self.parent, padding=(5, 0, 5, 2))
        f1.grid(row=1, column=0, sticky="ew")
        f1.columnconfigure(1, weight=1)
        self._mode_btn = ttk.Button(
            f1, text="フィットモード: OFF", command=self._toggle_mode, width=22
        )
        self._mode_btn.grid(row=0, column=0, padx=(0, 8))
        ttk.Label(f1, text="グラフ上をドラッグしてピーク範囲を選択").grid(
            row=0, column=1, sticky="w"
        )

        # --- 結果テーブル ---
        tree_frame = ttk.Frame(self.parent)
        tree_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=3)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        cols = ("file", "center", "fwhm", "d", "D", "r2", "rel")
        self._tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings",
            selectmode="browse", height=5,
        )
        headings = {
            "file": "ファイル", "center": "2θ (°)", "fwhm": "FWHM (°)",
            "d": "d (Å)", "D": "D (Å)", "r2": "R²", "rel": "信",
        }
        widths = {"file": 78, "center": 108, "fwhm": 108, "d": 65, "D": 90, "r2": 54, "rel": 26}
        for col, head in headings.items():
            self._tree.heading(col, text=head)
            self._tree.column(col, width=widths[col], anchor="center" if col != "file" else "w", minwidth=24)

        self._tree.tag_configure("good",    foreground="#2a8a2a")
        self._tree.tag_configure("caution", foreground="#b37400")
        self._tree.tag_configure("poor",    foreground="#cc2222")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self._tree.bind("<<TreeviewSelect>>", self._on_row_select)

        # --- ボタン・凡例 ---
        f3 = ttk.Frame(self.parent, padding=(5, 0, 5, 0))
        f3.grid(row=3, column=0, sticky="ew")
        ttk.Button(f3, text="選択行を削除", command=self._delete_selected).pack(side="left", padx=(0, 4))
        ttk.Button(f3, text="全クリア",     command=self._clear_all).pack(side="left", padx=(0, 4))
        ttk.Button(f3, text="コピー",       command=self._copy_to_clipboard).pack(side="left")

        ttk.Label(
            self.parent,
            text="✓ R²≥0.99かつFWHM≥0.1°   △ FWHM<0.1°(装置広がり)   ✗ R²<0.95",
            foreground="gray", font=("", 8),
        ).grid(row=4, column=0, sticky="w", padx=5)

        ttk.Label(
            self.parent, textvariable=self._error_var,
            foreground="red", wraplength=320,
        ).grid(row=5, column=0, sticky="w", padx=5)

        # --- 格子定数計算 ---
        lc = ttk.LabelFrame(self.parent, text="格子定数計算  (行を選択すると d が自動入力)")
        lc.grid(row=6, column=0, sticky="ew", padx=5, pady=(4, 2))
        lc.columnconfigure(1, weight=1)

        ttk.Label(lc, text="d (Å):").grid(row=0, column=0, sticky="w", padx=5, pady=3)
        ttk.Entry(lc, textvariable=self._d_var).grid(row=0, column=1, sticky="ew", padx=5, pady=3)

        hkl_f = ttk.Frame(lc)
        hkl_f.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=3)
        ttk.Label(hkl_f, text="面指数 (h, k, l):").pack(side="left")
        for v in (self._h_var, self._k_var, self._l_var):
            ttk.Entry(hkl_f, textvariable=v, width=4).pack(side="left", padx=2)

        ttk.Label(
            lc, textvariable=self._lc_result_var,
            relief="sunken", font=("", 10, "bold"),
        ).grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 5))

        # --- D の説明 ---
        dframe = ttk.LabelFrame(self.parent, text="結晶子サイズ D の解釈 (面直測定)")
        dframe.grid(row=7, column=0, sticky="ew", padx=5, pady=(2, 5))
        note = (
            "Scherrer式: D = 0.94·λ / (β·cosθ)  ← 面直方向の結晶秩序の長さ\n"
            "D < 100 Å    : ナノ結晶・高密度欠陥\n"
            "D 100–1000 Å : 通常の薄膜域\n"
            "D > 1000 Å   : 装置分解能限界付近（参考値）\n"
            "△ FWHM < 0.1° → 装置広がり補正が必要 → D を過大評価する可能性\n"
            "精度の目安: ±10–30%"
        )
        ttk.Label(dframe, text=note, justify="left", font=("", 8)).pack(
            anchor="w", padx=5, pady=3
        )

    # ------------------------------------------------------------------ #
    def _refresh_file_list(self):
        try:
            fps = list(self.app.file_listbox.get(0, tk.END))
            names = [self.app.file_data.get(fp, fp) for fp in fps]
            self._file_combo["values"] = names
            sel = self.app.file_listbox.curselection()
            if sel:
                self._file_combo.current(sel[0])
            elif names:
                self._file_combo.current(0)
        except Exception:
            pass

    def _on_file_combo_select(self, event):
        idx = self._file_combo.current()
        if idx < 0:
            return
        self.app.file_listbox.selection_clear(0, tk.END)
        self.app.file_listbox.selection_set(idx)
        self.app.file_listbox.see(idx)

    def _toggle_mode(self):
        if self.app.fit_handler.mode_active:
            self.app.fit_handler.disable_mode()
            self._mode_btn.config(text="フィットモード: OFF")
        else:
            self._refresh_file_list()
            self.app.fit_handler.enable_mode()
            self._mode_btn.config(text="フィットモード: ON ")

    # ------------------------------------------------------------------ #
    @staticmethod
    def _reliability(result):
        r2   = result.get("r_squared", 0.0)
        fwhm = result.get("fwhm", 0.0)
        if r2 < 0.95:
            return "✗", "poor"
        if fwhm < 0.10:
            return "△", "caution"
        return "✓", "good"

    def add_result(self, result):
        def _fmt(val, err=None, dec=3):
            if not math.isfinite(val):
                return "N/A"
            s = f"{val:.{dec}f}"
            if err is not None and math.isfinite(err):
                s += f" ±{err:.{dec}f}"
            return s

        rel_sym, tag = self._reliability(result)
        legend = result.get("legend", result.get("file", ""))
        display = legend[:10] + "…" if len(legend) > 11 else legend

        row = (
            display,
            _fmt(result["center"], result["center_err"], 3),
            _fmt(result["fwhm"],   result["fwhm_err"],   3),
            f"{result['d_spacing']:.4f}",
            _fmt(result["crystallite_size"], result["crystallite_size_err"], 0),
            f"{result['r_squared']:.4f}",
            rel_sym,
        )
        iid = self._tree.insert("", "end", values=row, tags=(tag,))
        self._rows.append((result, iid))
        self._tree.see(iid)

    def _on_row_select(self, event):
        sel = self._tree.selection()
        if not sel:
            return
        idx = self._tree.index(sel[0])
        if 0 <= idx < len(self._rows):
            self._d_var.set(f"{self._rows[idx][0]['d_spacing']:.4f}")

    def _update_lattice(self, *_):
        try:
            d = float(self._d_var.get())
            h = int(self._h_var.get())
            k = int(self._k_var.get())
            l = int(self._l_var.get())
            if h == 0 and k == 0 and l == 0:
                self._lc_result_var.set("エラー: (0,0,0) 不可")
                return
            if d <= 0:
                self._lc_result_var.set("エラー: d > 0 が必要")
                return
            a = d * math.sqrt(h ** 2 + k ** 2 + l ** 2)
            self._lc_result_var.set(f"a = {a:.4f} Å")
        except (ValueError, TypeError):
            self._lc_result_var.set("")

    # ------------------------------------------------------------------ #
    def show_error(self, msg):
        self._error_var.set(f"エラー: {msg}")

    def clear_error(self):
        self._error_var.set("")

    def _delete_selected(self):
        sel = self._tree.selection()
        if not sel:
            return
        iid = sel[0]
        index = next((i for i, (_, r) in enumerate(self._rows) if r == iid), None)
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
        header = "ファイル\t2θ (°)\tFWHM (°)\td (Å)\tD (Å)\tR²\t信頼性"
        rows = [
            "\t".join(self._tree.item(item, "values"))
            for item in self._tree.get_children()
        ]
        self.app.master.clipboard_clear()
        self.app.master.clipboard_append(header + "\n" + "\n".join(rows))
