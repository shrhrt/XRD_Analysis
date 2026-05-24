import tkinter as tk
from tkinter import ttk
from core import data_analyzer


class AnalysisTab:
    """解析ツールタブのUIとロジックを担当するクラス"""

    def __init__(self, parent, app):
        self.parent = parent
        self.app = app  # メインアプリ(XRDPlotter)への参照を保持
        self.build()

    def build(self):
        analysis_frame = ttk.Frame(self.parent, padding=(10, 10))
        analysis_frame.pack(fill="x", anchor="n")
        analysis_frame.columnconfigure(0, weight=1)

        # d-spacing tool
        d_spacing_frame = ttk.LabelFrame(analysis_frame, text="d値計算ツール")
        d_spacing_frame.grid(row=0, column=0, sticky="ew", pady=5)
        d_spacing_frame.columnconfigure(1, weight=1)
        ttk.Label(d_spacing_frame, text="ブラッグの式: nλ = 2d sin(θ)").grid(
            row=0, column=0, columnspan=3, sticky="w", padx=5
        )
        ttk.Label(d_spacing_frame, text="定数: X線=Co Kα1 (λ=1.78897 Å), n=1").grid(
            row=1, column=0, columnspan=3, sticky="w", padx=5
        )
        ttk.Label(d_spacing_frame, text="2θ (degree):").grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )

        d_input_entry = ttk.Entry(
            d_spacing_frame, textvariable=self.app.model.d_spacing_input_2theta_var
        )
        d_input_entry.grid(row=2, column=1, sticky="ew", padx=5)
        ttk.Button(d_spacing_frame, text="計算", command=self.calculate_d_spacing).grid(
            row=2, column=2, padx=5
        )
        ttk.Label(
            d_spacing_frame,
            textvariable=self.app.model.d_spacing_result_var,
            relief="sunken",
        ).grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        d_input_entry.bind("<Return>", self.calculate_d_spacing)

        # Lattice constant tool
        lc_frame = ttk.LabelFrame(
            analysis_frame, text="格子定数計算ツール (立方晶のみ)"
        )
        lc_frame.grid(row=1, column=0, sticky="ew", pady=5)
        lc_frame.columnconfigure(1, weight=1)
        ttk.Label(lc_frame, text="式: a = d * √(h² + k² + l²)").grid(
            row=0, column=0, columnspan=3, sticky="w", padx=5
        )
        ttk.Label(lc_frame, text="d-spacing (Å):").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )

        lc_d_entry = ttk.Entry(lc_frame, textvariable=self.app.model.lc_input_d_var)
        lc_d_entry.grid(row=1, column=1, sticky="ew", padx=5)
        ttk.Button(lc_frame, text="コピー", command=self.copy_d_spacing).grid(
            row=1, column=2, padx=5
        )

        hkl_frame = ttk.Frame(lc_frame)
        hkl_frame.grid(row=2, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        ttk.Label(hkl_frame, text="面指数 (h, k, l):").pack(side="left")
        ttk.Entry(hkl_frame, textvariable=self.app.model.lc_h_var, width=5).pack(
            side="left"
        )
        ttk.Entry(hkl_frame, textvariable=self.app.model.lc_k_var, width=5).pack(
            side="left"
        )
        ttk.Entry(hkl_frame, textvariable=self.app.model.lc_l_var, width=5).pack(
            side="left"
        )

        ttk.Button(lc_frame, text="計算", command=self.calculate_lattice_constant).grid(
            row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5
        )
        ttk.Label(
            lc_frame, textvariable=self.app.model.lc_result_var, relief="sunken"
        ).grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        # Peak detection
        peak_frame = ttk.LabelFrame(analysis_frame, text="ピーク検出")
        peak_frame.grid(row=2, column=0, sticky="ew", pady=5)
        peak_frame.columnconfigure(1, weight=1)
        ttk.Checkbutton(
            peak_frame,
            text="有効化",
            variable=self.app.model.peak_detection_enabled_var,
            command=self.app.schedule_update,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=5)

        # 基板除外スライダー（最大値の何%以上を基板とみなすか）
        ttk.Label(peak_frame, text="基板除外 (最大値の %):").grid(
            row=1, column=0, sticky="w", padx=5, pady=2
        )
        trim_frame = ttk.Frame(peak_frame)
        trim_frame.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        trim_frame.columnconfigure(0, weight=1)
        ttk.Scale(
            trim_frame,
            variable=self.app.model.peak_detection_trim_top_var,
            from_=0,
            to=10,
            orient="horizontal",
            command=lambda _: self.app.schedule_update(),
        ).grid(row=0, column=0, sticky="ew")
        trim_val_label = ttk.Label(trim_frame, text="0% (無効)", width=9)
        trim_val_label.grid(row=0, column=1, padx=(4, 0))

        def _update_trim_label(*_):
            v = self.app.model.peak_detection_trim_top_var.get()
            if v <= 0:
                trim_val_label.config(text="0% (無効)")
            else:
                trim_val_label.config(text=f"{v:.1f}%")

        self.app.model.peak_detection_trim_top_var.trace_add("write", _update_trim_label)

        ttk.Label(peak_frame, text="最小高さ (参照値の %):").grid(
            row=2, column=0, sticky="w", padx=5, pady=2
        )
        ttk.Spinbox(
            peak_frame,
            textvariable=self.app.model.peak_detection_height_var,
            from_=0,
            to=5,
            increment=0.5,
            command=self.app.schedule_update,
        ).grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(peak_frame, text="最小プロミネンス (参照値の %):").grid(
            row=3, column=0, sticky="w", padx=5, pady=2
        )
        ttk.Spinbox(
            peak_frame,
            textvariable=self.app.model.peak_detection_prominence_var,
            from_=0,
            to=5,
            increment=0.5,
            command=self.app.schedule_update,
        ).grid(row=3, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(peak_frame, text="最小幅 (degree):").grid(
            row=4, column=0, sticky="w", padx=5, pady=2
        )
        ttk.Spinbox(
            peak_frame,
            textvariable=self.app.model.peak_detection_width_var,
            from_=0.01,
            to=0.1,
            increment=0.01,
            command=self.app.schedule_update,
        ).grid(row=4, column=1, sticky="ew", padx=5, pady=2)

        # Substrate peak detection
        substrate_frame = ttk.LabelFrame(analysis_frame, text="基板ピーク検出 (赤)")
        substrate_frame.grid(row=3, column=0, sticky="ew", pady=5)
        substrate_frame.columnconfigure(1, weight=1)
        ttk.Label(
            substrate_frame,
            text="全データ最大値を基準に強いピークを検出します",
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=5)
        ttk.Checkbutton(
            substrate_frame,
            text="有効化",
            variable=self.app.model.substrate_peak_detection_enabled_var,
            command=self.app.schedule_update,
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=5)
        ttk.Label(substrate_frame, text="最小高さ (最大値の %):").grid(
            row=2, column=0, sticky="w", padx=5, pady=2
        )
        ttk.Spinbox(
            substrate_frame,
            textvariable=self.app.model.substrate_peak_detection_height_var,
            from_=1,
            to=100,
            increment=1,
            command=self.app.schedule_update,
        ).grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(substrate_frame, text="最小幅 (degree):").grid(
            row=3, column=0, sticky="w", padx=5, pady=2
        )
        ttk.Spinbox(
            substrate_frame,
            textvariable=self.app.model.substrate_peak_detection_width_var,
            from_=0.01,
            to=10,
            increment=0.05,
            command=self.app.schedule_update,
        ).grid(row=3, column=1, sticky="ew", padx=5, pady=2)

    def calculate_d_spacing(self, *args):
        try:
            two_theta_deg = float(self.app.model.d_spacing_input_2theta_var.get())
            d = data_analyzer.calculate_d_value(two_theta_deg)
            self.app.model.d_spacing_result_var.set(f"{d:.5f} Å")
        except ValueError as e:
            self.app.model.d_spacing_result_var.set(f"エラー: {e}")
        except (ValueError, TypeError):
            self.app.model.d_spacing_result_var.set(
                "エラー: 有効な数値を入力してください"
            )

    def copy_d_spacing(self, *args):
        try:
            result_str = self.app.model.d_spacing_result_var.get()
            d_value = result_str.split(" ")[0]
            float(d_value)
            self.app.model.lc_input_d_var.set(d_value)
        except (ValueError, IndexError):
            pass

    def calculate_lattice_constant(self, *args):
        try:
            d = float(self.app.model.lc_input_d_var.get())
            h = int(self.app.model.lc_h_var.get())
            k = int(self.app.model.lc_k_var.get())
            l = int(self.app.model.lc_l_var.get())
            a = data_analyzer.calculate_lattice_constant(d, h, k, l)
            self.app.model.lc_result_var.set(f"a = {a:.5f} Å")
        except ValueError as e:
            self.app.model.lc_result_var.set(f"エラー: {e}")
        except (ValueError, TypeError):
            self.app.model.lc_result_var.set("エラー: 有効な数値を入力してください")
