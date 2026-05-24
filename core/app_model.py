import tkinter as tk


class AppStateModel:
    """
    アプリケーションの状態（各種設定値、入力値など）を一元管理するモデルクラス。
    UI(View)とロジック(Controller/ViewModel)の分離を目的としています。
    """

    def __init__(self):
        # --- プロット設定関連 ---
        self.xmin_var = tk.StringVar(value="30")
        self.xmax_var = tk.StringVar(value="130")
        self.threshold_var = tk.StringVar(value="1")
        self.legend_name_var = tk.StringVar()
        self.show_legend_var = tk.BooleanVar(value=True)
        self.stack_plots_var = tk.BooleanVar(value=False)
        self.legend_loc_var = tk.StringVar(value="best")
        self.legend_frame_var = tk.BooleanVar(value=True)
        self.legend_bgcolor_var = tk.StringVar(value="white")
        self.legend_italic_var = tk.BooleanVar(value=False)
        self.threshold_handling_var = tk.StringVar(value="clip")
        self.yscale_var = tk.StringVar(value="log")
        self.font_family_var = tk.StringVar(value="sans-serif")
        self.plot_spacing_var = tk.DoubleVar(value=3)

        # --- 外観設定関連 ---
        self.xlabel_var = tk.StringVar(value="2θ/ω (degree)")
        self.ylabel_var = tk.StringVar(value="Log Intensity (arb. Units)")
        self.axis_label_fontsize_var = tk.DoubleVar(value=20)
        self.tick_label_fontsize_var = tk.DoubleVar(value=16)
        self.legend_fontsize_var = tk.DoubleVar(value=10)
        self.plot_linewidth_var = tk.DoubleVar(value=1.0)
        self.tick_direction_var = tk.StringVar(value="in")
        self.xaxis_major_tick_spacing_var = tk.DoubleVar(value=5)
        self.show_grid_var = tk.BooleanVar(value=False)
        self.ytop_padding_factor_var = tk.DoubleVar(value=1.5)
        self.hide_major_xtick_labels_var = tk.BooleanVar(value=False)
        self.show_minor_xticks_var = tk.BooleanVar(value=True)
        self.xminor_tick_spacing_var = tk.DoubleVar(value=1.0)
        self.match_math_font_var = tk.BooleanVar(value=False)

        # --- 解析ツール関連 ---
        self.d_spacing_input_2theta_var = tk.StringVar()
        self.d_spacing_result_var = tk.StringVar(value="d-spacing (Å)")
        self.lc_input_d_var = tk.StringVar()
        self.lc_h_var = tk.StringVar(value="1")
        self.lc_k_var = tk.StringVar(value="0")
        self.lc_l_var = tk.StringVar(value="0")
        self.lc_result_var = tk.StringVar(value="a = ?")

        self.peak_detection_enabled_var = tk.BooleanVar(value=False)
        self.peak_detection_trim_top_var = tk.DoubleVar(value=1.0)    # 基板除外閾値 (最大値の %) — 0=無効
        self.peak_detection_height_var = tk.DoubleVar(value=1.0)      # 基板除外後の最大値の %
        self.peak_detection_prominence_var = tk.DoubleVar(value=2.0)  # 基板除外後の最大値の %
        self.peak_detection_width_var = tk.DoubleVar(value=0.06)      # degree

        self.substrate_peak_detection_enabled_var = tk.BooleanVar(value=False)
        self.substrate_peak_detection_height_var = tk.DoubleVar(value=20.0)  # 最大値の %
        self.substrate_peak_detection_width_var = tk.DoubleVar(value=0.05)   # degree

        # --- 参照ピーク関連 ---
        self.peak_label_fontsize_var = tk.DoubleVar(value=9)
        self.peak_label_offset_var = tk.DoubleVar(value=0.4)
        self.peak_label_y_var = tk.DoubleVar(value=0.90)

        self.peak_name_vars = []
        self.peak_angle_vars = []
        self.peak_visible_vars = []
        self.peak_color_vars = []
        self.peak_style_vars = []

        # --- テキストアノテーション ---
        self.annotation_visible_var = tk.BooleanVar(value=False)
        self.annotation_text_var = tk.StringVar(value="")
        self.annotation_x_var = tk.DoubleVar(value=0.72)
        self.annotation_y_var = tk.DoubleVar(value=0.95)
        self.annotation_fontsize_var = tk.DoubleVar(value=12)

        # --- エクスポート関連 ---
        self.export_width_var = tk.StringVar(value="6")
        self.export_height_var = tk.StringVar(value="6")
        self.export_format_var = tk.StringVar(value="png")

        self.selected_substance_var = tk.StringVar()

        # 保存対象の変数名リスト（動的に取得する設計）
        self.savable_vars = [
            attr
            for attr in dir(self)
            if not callable(getattr(self, attr))
            and not attr.startswith("__")
            and attr.endswith("_var")
        ]
