import os
import logging
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, NullLocator
import numpy as np
import math
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass, field
from scipy.signal import find_peaks
from scipy.optimize import curve_fit

logger = logging.getLogger(__name__)


# parse_ras_file は draw_plot から切り離され、呼び出し元で処理される
def parse_ras_file(filepath: str) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Rigaku RAS形式のファイルを読み込み、角度と強度のデータを抽出。

    Args:
        filepath (str): 読み込む.rasファイルのパス

    Returns:
        Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
            (角度のNumpy配列, 強度のNumpy配列)。読み込みに失敗した場合は (None, None) を返す。
    """
    angles, intensities = [], []
    data_started = False
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                stripped_line = line.strip()

                # データセクションの開始と終了の検知
                if stripped_line == "*RAS_INT_START":
                    data_started = True
                    continue
                elif stripped_line == "*RAS_INT_END":
                    break

                # データ行の解析
                if data_started:
                    parts = stripped_line.split()
                    if len(parts) >= 2:
                        try:
                            angles.append(float(parts[0]))
                            intensities.append(float(parts[1]))
                        except ValueError:
                            # 数値に変換できない行（ヘッダーなど）はスキップ
                            continue
    except OSError as e:
        logger.error(f"Error reading file {filepath}: {e}")
        return None, None

    return np.array(angles, dtype=float), np.array(intensities, dtype=float)


def calculate_d_value(two_theta_deg: float, wavelength: float = 1.78897) -> float:
    """ブラッグの法則からd値を計算する (n=1)"""
    if two_theta_deg <= 0 or two_theta_deg >= 180:
        raise ValueError("2θは0より大きく180未満である必要があります。")
    theta_rad = math.radians(two_theta_deg / 2.0)
    return wavelength / (2 * math.sin(theta_rad))


def calculate_lattice_constant(d: float, h: int, k: int, l: int) -> float:
    """立方晶の格子定数を計算する"""
    if h**2 + k**2 + l**2 == 0:
        raise ValueError("(h,k,l)は(0,0,0)にできません。")
    if d <= 0:
        raise ValueError("d値は正の数である必要があります。")
    return d * math.sqrt(h**2 + k**2 + l**2)


def _gaussian_with_bg(x, A, x0, sigma, a, b):
    """Gaussian + 線形バックグラウンド"""
    return A * np.exp(-((x - x0) ** 2) / (2.0 * sigma ** 2)) + a * x + b


def fit_peak_gaussian(
    angles: np.ndarray,
    intensities: np.ndarray,
    angle_min: float,
    angle_max: float,
) -> Dict[str, Any]:
    """
    指定範囲に Gaussian + 線形バックグラウンドをフィット。

    Returns:
        center, center_err, fwhm, fwhm_err, d_spacing,
        crystallite_size, crystallite_size_err, r_squared, x_fit, y_fit
    Raises:
        ValueError: データ不足またはフィット失敗時
    """
    mask = (
        (angles >= angle_min)
        & (angles <= angle_max)
        & np.isfinite(intensities)
        & (intensities > 0)
    )
    x = angles[mask]
    y = intensities[mask]

    if len(x) < 5:
        raise ValueError(f"範囲内のデータ点が {len(x)} 点しかありません（5点以上必要）")

    peak_idx = int(np.argmax(y))
    x0_init = float(x[peak_idx])
    A_init = max(float(y[peak_idx] - np.min(y)), float(y[peak_idx]) * 0.1)
    sigma_init = (angle_max - angle_min) / 4.0
    span = float(x[-1] - x[0])
    a_init = float((y[-1] - y[0]) / span) if span > 0 else 0.0
    b_init = float(y[0] - a_init * x[0])

    p0 = [A_init, x0_init, sigma_init, a_init, b_init]
    bounds = (
        [0.0, angle_min, 1e-6, -np.inf, -np.inf],
        [np.inf, angle_max, angle_max - angle_min, np.inf, np.inf],
    )

    try:
        popt, pcov = curve_fit(
            _gaussian_with_bg, x, y, p0=p0, bounds=bounds, maxfev=10000
        )
    except RuntimeError:
        raise ValueError("フィットが収束しませんでした。範囲を変えてみてください。")
    except ValueError as exc:
        raise ValueError(f"フィットエラー: {exc}") from exc

    perr = np.sqrt(np.diag(pcov))
    _, x0, sigma, _, _ = popt
    fwhm = 2.3548195 * abs(sigma)
    fwhm_err = 2.3548195 * float(perr[2])

    y_pred = _gaussian_with_bg(x, *popt)
    ss_res = float(np.sum((y - y_pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    d_val = calculate_d_value(float(x0))
    D = scherrer(fwhm, float(x0))
    D_err = D * (fwhm_err / fwhm) if math.isfinite(D) and fwhm > 0 else float("nan")

    x_dense = np.linspace(angle_min, angle_max, 300)
    y_dense = _gaussian_with_bg(x_dense, *popt)

    return {
        "center": float(x0),
        "center_err": float(perr[1]),
        "fwhm": fwhm,
        "fwhm_err": fwhm_err,
        "d_spacing": d_val,
        "crystallite_size": D,
        "crystallite_size_err": D_err,
        "r_squared": r_squared,
        "x_fit": x_dense,
        "y_fit": y_dense,
    }


def scherrer(
    fwhm_deg: float,
    two_theta_deg: float,
    K: float = 0.94,
    wavelength: float = 1.78897,
) -> float:
    """シェラー式: D = K·λ / (β·cosθ)  [単位: Å]"""
    if fwhm_deg <= 0:
        return float("nan")
    beta_rad = math.radians(fwhm_deg)
    theta_rad = math.radians(two_theta_deg / 2.0)
    cos_theta = math.cos(theta_rad)
    if cos_theta <= 0:
        return float("nan")
    return (K * wavelength) / (beta_rad * cos_theta)


def _detect_peaks(
    angles: np.ndarray,
    intensities: np.ndarray,
    settings: Dict[str, Any],
) -> Tuple[np.ndarray, np.ndarray]:
    """
    ピーク検出を行い、検出されたピークの角度と強度を返す。
    入力データは変更しない。NaN/Inf を含むデータにも対応。

    height/prominence は最大強度に対する割合(%)で指定する。
    width は角度(degree)単位で指定する。

    Returns:
        (peak_angles, peak_intensities): 空配列は「ピークなし」を意味する。
    """
    if not settings.get("enabled", False):
        return np.array([]), np.array([])

    # NaN/Inf を除去した有効データのみを対象にする
    valid = np.isfinite(intensities)
    clean_angles = angles[valid]
    clean_intensities = intensities[valid]

    if clean_intensities.size < 3:
        return np.array([]), np.array([])

    # 基板除外: 最大値の trim_top_pct% 以上を基板領域とみなし除外する。
    # 0 のとき除外なし（全データ対象）。
    trim_top_pct = settings.get("trim_top_pct", 0.0)
    if trim_top_pct > 0:
        global_max = float(np.max(clean_intensities))
        substrate_threshold = (trim_top_pct / 100.0) * global_max
        film_mask = clean_intensities <= substrate_threshold
    else:
        film_mask = np.ones(len(clean_intensities), dtype=bool)

    film_intensities = clean_intensities[film_mask]
    if film_intensities.size < 3:
        return np.array([]), np.array([])

    data_max = float(np.max(film_intensities))
    if data_max <= 0:
        return np.array([]), np.array([])

    # height/prominence: 基板除外後の最大値に対する % → 絶対値に変換
    effective_height = (settings.get("min_height", 0.0) / 100.0) * data_max
    effective_prominence = (settings.get("min_prominence", 0.0) / 100.0) * data_max

    # width: 角度(degree) → データポイント数に変換（元のステップを使用）
    step = float(np.median(np.diff(clean_angles))) if clean_angles.size >= 2 else 1.0
    min_width_deg = settings.get("min_width", 0.0)
    effective_width = max(1.0, min_width_deg / step) if step > 0 else 1.0

    # 基板除外で生じたギャップで連続セグメントに分割して find_peaks を実行する。
    # セグメントの端点は両隣データがないため局所最大値と判定されず、
    # 基板裾のショルダー点が誤検出されなくなる。
    film_indices = np.where(film_mask)[0]
    gaps = np.where(np.diff(film_indices) > 1)[0] + 1
    segments = np.split(film_indices, gaps)

    all_peak_angles: list = []
    all_peak_heights: list = []
    for seg_idx in segments:
        if seg_idx.size < 3:
            continue
        seg_int = clean_intensities[seg_idx]
        peaks, props = find_peaks(
            seg_int,
            height=effective_height,
            prominence=effective_prominence,
            width=effective_width,
        )
        if peaks.size > 0:
            all_peak_angles.extend(clean_angles[seg_idx[peaks]])
            all_peak_heights.extend(props["peak_heights"])

    if not all_peak_angles:
        return np.array([]), np.array([])
    return np.array(all_peak_angles), np.array(all_peak_heights)


def _detect_substrate_peaks(
    angles: np.ndarray,
    intensities: np.ndarray,
    settings: Dict[str, Any],
) -> Tuple[np.ndarray, np.ndarray]:
    """
    基板ピーク（グローバル最大値基準で支配的に強いピーク）を検出する。
    _detect_peaks とは異なりグローバル最大値を参照値に使うため、
    薄膜ピークよりはるかに強い基板ピークを選別できる。

    height は全データ最大値に対する % で指定する。
    """
    if not settings.get("enabled", False):
        return np.array([]), np.array([])

    valid = np.isfinite(intensities)
    clean_angles = angles[valid]
    clean_intensities = intensities[valid]

    if clean_intensities.size < 3:
        return np.array([]), np.array([])

    data_max = float(np.max(clean_intensities))
    if data_max <= 0:
        return np.array([]), np.array([])

    effective_height = (settings.get("min_height", 0.0) / 100.0) * data_max

    step = float(np.median(np.diff(clean_angles))) if clean_angles.size >= 2 else 1.0
    min_width_deg = settings.get("min_width", 0.0)
    effective_width = max(1.0, min_width_deg / step) if step > 0 else 1.0

    peaks, properties = find_peaks(
        clean_intensities,
        height=effective_height,
        width=effective_width,
    )

    if peaks.size == 0:
        return np.array([]), np.array([])

    return clean_angles[peaks], properties["peak_heights"]


def _find_and_draw_peaks(
    ax: plt.Axes,
    angles: np.ndarray,
    intensities: np.ndarray,
    ymax: float,
    settings: Dict[str, Any],
):
    """検出されたピークをプロット上にテキストとして描画する。"""
    peak_angles, peak_intensities = _detect_peaks(angles, intensities, settings)

    for angle, intensity in zip(peak_angles, peak_intensities):
        ax.text(
            angle,
            intensity,
            f"{angle:.1f}°",
            verticalalignment="bottom",
            horizontalalignment="center",
            color="purple",
            fontsize=8,
            fontweight="bold",
        )


def _find_and_draw_substrate_peaks(
    ax: plt.Axes,
    angles: np.ndarray,
    intensities: np.ndarray,
    ymax: float,
    settings: Dict[str, Any],
):
    """検出された基板ピークをプロット上に赤テキストで描画する。"""
    peak_angles, peak_intensities = _detect_substrate_peaks(angles, intensities, settings)

    for angle, intensity in zip(peak_angles, peak_intensities):
        ax.text(
            angle,
            intensity,
            f"Sub:{angle:.1f}°",
            verticalalignment="bottom",
            horizontalalignment="center",
            color="red",
            fontsize=8,
            fontweight="bold",
        )


def _draw_reference_peaks(
    ax: plt.Axes,
    peaks_to_plot: List[Dict[str, Any]],
    ymax: float,
    appearance: Dict[str, Any],
):
    """
    参照ピーク（既知の物質の回折角度）を垂直線としてグラフ上に描画。

    Args:
        ax (plt.Axes): 描画先のMatplotlib Axesオブジェクト
        peaks_to_plot (List[Dict[str, Any]]): 描画する参照ピークのリスト
        ymax (float): グラフのY軸最大値
        appearance (Dict[str, Any]): 外観設定（フォントサイズなど）
    """
    if not peaks_to_plot:
        return

    peak_fontsize = appearance.get("peak_label_fontsize", 9)
    offset = appearance.get("peak_label_offset", 0.4)
    label_y = appearance.get("peak_label_y", 0.9)

    for peak in peaks_to_plot:
        if not peak.get("visible", False):
            continue
        name, angle = peak.get("name", ""), peak.get("angle")
        color, linestyle = peak.get("color", "black"), peak.get("linestyle", "--")
        if angle is not None:
            ax.axvline(
                x=angle, color=color, linestyle=linestyle, linewidth=1.2, ymax=1.0
            )
            ax.text(
                angle + offset,
                label_y,
                name,
                rotation=90,
                verticalalignment="top",
                horizontalalignment="left",
                color=color,
                fontsize=peak_fontsize,
                fontweight="bold",
                transform=ax.get_xaxis_transform(),
            )


@dataclass
class PlotSettings:
    """プロットに関する各種設定を保持するデータクラス"""

    threshold: float
    x_range: Tuple[Optional[float], Optional[float]]
    show_legend: bool
    stack: bool
    spacing: float
    appearance: Dict[str, Any]
    reference_peaks: List[Dict[str, Any]] = field(default_factory=list)
    peak_detection_settings: Optional[Dict[str, Any]] = None
    substrate_peak_detection_settings: Optional[Dict[str, Any]] = None
    legend_position: Optional[Tuple[float, float]] = None


def draw_plot(
    ax: plt.Axes,
    plot_data_full: List[Dict[str, Any]],
    settings: PlotSettings,
) -> Optional[str]:
    # 以降のコード変更を最小限にするため、設定値をローカル変数に展開
    threshold = settings.threshold
    x_range = settings.x_range
    reference_peaks = settings.reference_peaks
    show_legend = settings.show_legend
    stack = settings.stack
    spacing = settings.spacing
    appearance = settings.appearance
    peak_detection_settings = settings.peak_detection_settings
    substrate_peak_detection_settings = settings.substrate_peak_detection_settings
    legend_position = settings.legend_position

    ax.clear()

    linewidth = appearance.get("linewidth", 1.0)
    legend_fontsize = appearance.get("legend_fontsize", 10)
    ytop_padding_factor = appearance.get("ytop_padding_factor", 1.5)
    threshold_handling = appearance.get(
        "threshold_handling", "hide"
    )  # 'hide' or 'clip'
    yscale = appearance.get("yscale", "log")
    font_family = appearance.get("font_family", "sans-serif")

    color_sequence = [
        "red",
        "#001aff",
        "#32CD32",
        "#FF8C00",
        "#9400D3",
        "#00CED1",
        "#FF1493",
        "#1E90FF",
        "#FFD700",
        "#ADFF2F",
    ]

    all_plot_points_y = []
    current_multiplier_factor = 10**spacing  # 各プロット間での乗算係数

    processed_data = []

    # ステップ0: データを準備
    for item in plot_data_full:
        angles = item["angles"]
        intensities = np.array(item["intensities"], dtype=float)

        processed_data.append(
            {"label": item["label"], "angles": angles, "intensities": intensities}
        )

    # ステップ1: 全てのプロット対象データからY値を収集し、Y軸の範囲を決定する
    first_plot_lowest_y_val = None
    for idx, item in enumerate(processed_data):
        intensities_np = item["intensities"]
        # 閾値より大きいデータのみを範囲計算の対象とする
        valid_intensities = intensities_np[intensities_np >= threshold]

        if valid_intensities.size == 0:
            continue

        if stack:
            current_multiplier = current_multiplier_factor**idx
            plot_intensities = valid_intensities * current_multiplier
            if idx == 0:
                with np.errstate(all="ignore"):
                    first_plot_lowest_y_val = np.nanmin(plot_intensities)
        else:
            plot_intensities = valid_intensities

        all_plot_points_y.extend(plot_intensities)

    # ステップ2: Y軸の範囲を計算
    if not all_plot_points_y or np.all(np.isnan(all_plot_points_y)):
        ymin_val, ymax_val = (1, 10) if yscale == "log" else (0, 100)
    else:
        with np.errstate(all="ignore"):
            min_all_y = np.nanmin(all_plot_points_y)
            ymax_val = np.nanmax(all_plot_points_y) * ytop_padding_factor
        if (
            stack
            and first_plot_lowest_y_val is not None
            and not np.isnan(first_plot_lowest_y_val)
        ):
            ymin_val = first_plot_lowest_y_val
        else:
            ymin_val = min_all_y

    # ステップ3: データをプロットする。この際に閾値処理を適用する
    for idx, item in enumerate(processed_data):
        angles = item["angles"]
        intensities_np = item["intensities"].copy()  # 元データを破壊しないようコピー

        if threshold_handling == "hide":
            intensities_np[(intensities_np < threshold) | (intensities_np <= 0)] = (
                np.nan
            )
        elif threshold_handling == "clip":
            # 閾値より小さい値をクリップする。スタック表示の場合、スケーリング前の最小値だと問題があるので、
            # 閾値自体にクリップするのが素直。
            clip_val = threshold if threshold > 0 else ymin_val
            intensities_np[intensities_np < threshold] = clip_val
            intensities_np[intensities_np <= 0] = clip_val

        if np.all(np.isnan(intensities_np)):
            continue

        current_color = color_sequence[idx % len(color_sequence)]

        # ピーク検出はスタック表示のスケーリング前に実施
        if (
            peak_detection_settings
            and peak_detection_settings.get("enabled", False)
            and not stack
        ):
            _find_and_draw_peaks(
                ax, angles, intensities_np, ymax_val, peak_detection_settings
            )

        if (
            substrate_peak_detection_settings
            and substrate_peak_detection_settings.get("enabled", False)
            and not stack
        ):
            _find_and_draw_substrate_peaks(
                ax, angles, intensities_np, ymax_val, substrate_peak_detection_settings
            )

        if stack:
            current_multiplier = current_multiplier_factor**idx
            intensities_np = intensities_np * current_multiplier
            if peak_detection_settings and peak_detection_settings.get("enabled", False):
                # スケーリング後の強度を渡す。height/prominence は内部で最大値基準の%に変換される
                _find_and_draw_peaks(
                    ax, angles, intensities_np, ymax_val, peak_detection_settings
                )
            if substrate_peak_detection_settings and substrate_peak_detection_settings.get("enabled", False):
                _find_and_draw_substrate_peaks(
                    ax, angles, intensities_np, ymax_val, substrate_peak_detection_settings
                )

        ax.plot(
            angles,
            intensities_np,
            label=item["label"],
            linewidth=linewidth,
            color=current_color,
        )

    ax.set_ylim(bottom=ymin_val, top=ymax_val)

    ax.set_xlabel(
        appearance.get("xlabel", "2θ/ω (degree)"),
        fontsize=appearance.get("axis_label_fontsize", 20),
        fontfamily=font_family,
    )
    ax.set_ylabel(
        appearance.get("ylabel", "Log Intensity (arb. Units)"),
        fontsize=appearance.get("axis_label_fontsize", 20),
        fontfamily=font_family,
    )

    ax.tick_params(
        axis="x",
        which="major",
        direction=appearance.get("tick_direction", "in"),
        labelsize=appearance.get("tick_label_fontsize", 16),
        top=True,
        labeltop=False,
    )
    ax.tick_params(
        axis="x", labelbottom=not appearance.get("hide_major_xtick_labels", False)
    )

    ax.set_xlim(x_range[0], x_range[1])
    ax.set_yscale(yscale)
    ax.xaxis.set_major_locator(
        MultipleLocator(appearance.get("xaxis_major_tick_spacing", 10))
    )

    if appearance.get("show_minor_xticks", False):
        ax.xaxis.set_minor_locator(
            MultipleLocator(appearance.get("xminor_tick_spacing", 1.0))
        )
        ax.tick_params(
            axis="x",
            which="minor",
            direction=appearance.get("tick_direction", "in"),
            bottom=True,
            top=True,
        )
    else:
        ax.xaxis.set_minor_locator(NullLocator())

    # Y軸の目盛りを非表示にする
    ax.yaxis.set_major_locator(NullLocator())
    ax.yaxis.set_minor_locator(NullLocator())

    if appearance.get("show_grid", False):
        ax.grid(True, axis="x", which="both", ls="--", linewidth=0.5)
    else:
        ax.grid(False)

    if show_legend:
        frameon = appearance.get("legend_frame", True)
        facecolor = appearance.get("legend_bgcolor", "white")
        if legend_position:
            leg = ax.legend(
                fontsize=legend_fontsize,
                loc="lower left",
                bbox_to_anchor=legend_position,
                frameon=frameon,
                facecolor=facecolor,
            )
        else:
            loc = appearance.get("legend_loc", "best")
            leg = ax.legend(
                fontsize=legend_fontsize, loc=loc, frameon=frameon, facecolor=facecolor
            )
            if leg:
                leg.set_draggable(True)
        if leg:
            style = "italic" if appearance.get("legend_italic", False) else "normal"
            plt.setp(leg.get_texts(), fontfamily=font_family, style=style)

    # Apply font to tick labels
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontfamily(font_family)

    _draw_reference_peaks(
        ax, reference_peaks, ymax=ax.get_ylim()[1], appearance=appearance
    )

    if appearance.get("annotation_visible", False):
        ann_text = appearance.get("annotation_text", "")
        if ann_text:
            ax.text(
                appearance.get("annotation_x", 0.72),
                appearance.get("annotation_y", 0.95),
                ann_text,
                transform=ax.transAxes,
                fontsize=appearance.get("annotation_fontsize", 12),
                verticalalignment="top",
                fontfamily=font_family,
            )

    return None
