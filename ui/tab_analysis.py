import tkinter as tk
from tkinter import ttk
import math


class AnalysisTab:
    """解析ツールタブのUIとロジックを担当するクラス"""

    def __init__(self, parent, app):
        self.parent = parent
        self.app = app  # メインアプリ(XRDPlotter)への参照を保持
        self.build()

    def build(self):
        analysis_frame = tk.Frame(self.parent, padx=10, pady=10)
        analysis_frame.pack(fill="x", anchor="n")
        analysis_frame.columnconfigure(0, weight=1)

        # d-spacing tool
        d_spacing_frame = tk.LabelFrame(analysis_frame, text="d値計算ツール")
        d_spacing_frame.grid(row=0, column=0, sticky="ew", pady=5)
        d_spacing_frame.columnconfigure(1, weight=1)
        tk.Label(d_spacing_frame, text="ブラッグの式: nλ = 2d sin(θ)").grid(
            row=0, column=0, columnspan=3, sticky="w", padx=5
        )
        tk.Label(d_spacing_frame, text="定数: X線=Co Kα1 (λ=1.78897 Å), n=1").grid(
            row=1, column=0, columnspan=3, sticky="w", padx=5
        )
        tk.Label(d_spacing_frame, text="2θ (degree):").grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )

        d_input_entry = tk.Entry(
            d_spacing_frame, textvariable=self.app.d_spacing_input_2theta_var
        )
        d_input_entry.grid(row=2, column=1, sticky="ew", padx=5)
        tk.Button(d_spacing_frame, text="計算", command=self.calculate_d_spacing).grid(
            row=2, column=2, padx=5
        )
        tk.Label(
            d_spacing_frame, textvariable=self.app.d_spacing_result_var, relief="sunken"
        ).grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        d_input_entry.bind("<Return>", self.calculate_d_spacing)

        # Lattice constant tool
        lc_frame = tk.LabelFrame(analysis_frame, text="格子定数計算ツール (立方晶のみ)")
        lc_frame.grid(row=1, column=0, sticky="ew", pady=5)
        lc_frame.columnconfigure(1, weight=1)
        tk.Label(lc_frame, text="式: a = d * √(h² + k² + l²)").grid(
            row=0, column=0, columnspan=3, sticky="w", padx=5
        )
        tk.Label(lc_frame, text="d-spacing (Å):").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )

        lc_d_entry = tk.Entry(lc_frame, textvariable=self.app.lc_input_d_var)
        lc_d_entry.grid(row=1, column=1, sticky="ew", padx=5)
        tk.Button(lc_frame, text="コピー", command=self.copy_d_spacing).grid(
            row=1, column=2, padx=5
        )

        hkl_frame = tk.Frame(lc_frame)
        hkl_frame.grid(row=2, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        tk.Label(hkl_frame, text="面指数 (h, k, l):").pack(side="left")
        tk.Entry(hkl_frame, textvariable=self.app.lc_h_var, width=5).pack(side="left")
        tk.Entry(hkl_frame, textvariable=self.app.lc_k_var, width=5).pack(side="left")
        tk.Entry(hkl_frame, textvariable=self.app.lc_l_var, width=5).pack(side="left")

        tk.Button(lc_frame, text="計算", command=self.calculate_lattice_constant).grid(
            row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5
        )
        tk.Label(lc_frame, textvariable=self.app.lc_result_var, relief="sunken").grid(
            row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=5
        )

        # Peak detection
        peak_frame = tk.LabelFrame(analysis_frame, text="ピーク検出")
        peak_frame.grid(row=2, column=0, sticky="ew", pady=5)
        peak_frame.columnconfigure(1, weight=1)
        tk.Checkbutton(
            peak_frame,
            text="有効化",
            variable=self.app.peak_detection_enabled_var,
            command=self.app.schedule_update,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=5)
        tk.Label(peak_frame, text="最小高さ:").grid(
            row=1, column=0, sticky="w", padx=5, pady=2
        )
        ttk.Spinbox(
            peak_frame,
            textvariable=self.app.peak_detection_height_var,
            from_=0,
            to=1e9,
            increment=10,
            command=self.app.schedule_update,
        ).grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        tk.Label(peak_frame, text="最小プロミネンス:").grid(
            row=2, column=0, sticky="w", padx=5, pady=2
        )
        ttk.Spinbox(
            peak_frame,
            textvariable=self.app.peak_detection_prominence_var,
            from_=0,
            to=1e9,
            increment=10,
            command=self.app.schedule_update,
        ).grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        tk.Label(peak_frame, text="最小幅:").grid(
            row=3, column=0, sticky="w", padx=5, pady=2
        )
        ttk.Spinbox(
            peak_frame,
            textvariable=self.app.peak_detection_width_var,
            from_=0,
            to=100,
            increment=0.5,
            command=self.app.schedule_update,
        ).grid(row=3, column=1, sticky="ew", padx=5, pady=2)

    def calculate_d_spacing(self, *args):
        try:
            two_theta_deg = float(self.app.d_spacing_input_2theta_var.get())
            if two_theta_deg <= 0 or two_theta_deg >= 180:
                self.app.d_spacing_result_var.set("エラー: 2θは0-180の範囲で入力")
                return
            theta_rad = math.radians(two_theta_deg / 2.0)
            lambda_coka1 = 1.78897
            d = lambda_coka1 / (2 * math.sin(theta_rad))
            self.app.d_spacing_result_var.set(f"{d:.5f} Å")
        except (ValueError, TypeError):
            self.app.d_spacing_result_var.set("エラー: 有効な数値を入力してください")

    def copy_d_spacing(self, *args):
        try:
            result_str = self.app.d_spacing_result_var.get()
            d_value = result_str.split(" ")[0]
            float(d_value)
            self.app.lc_input_d_var.set(d_value)
        except (ValueError, IndexError):
            pass

    def calculate_lattice_constant(self, *args):
        try:
            d = float(self.app.lc_input_d_var.get())
            h = int(self.app.lc_h_var.get())
            k = int(self.app.lc_k_var.get())
            l = int(self.app.lc_l_var.get())
            if (h**2 + k**2 + l**2) == 0:
                self.app.lc_result_var.set("エラー: (h,k,l)は(0,0,0)にできません")
                return
            a = d * math.sqrt(h**2 + k**2 + l**2)
            self.app.lc_result_var.set(f"a = {a:.5f} Å")
        except (ValueError, TypeError):
            self.app.lc_result_var.set("エラー: 有効な数値を入力してください")
