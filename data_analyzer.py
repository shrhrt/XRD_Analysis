import os
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, NullLocator
import numpy as np
from typing import List, Tuple, Dict, Optional, Any
from scipy.ndimage import minimum_filter1d
from scipy.signal import find_peaks

# parse_ras_file は draw_plot から切り離され、呼び出し元で処理される
def parse_ras_file(filepath: str) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    angles, intensities = [], []
    data_started = False
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.strip() == '*RAS_INT_START': data_started = True; continue
                if line.strip() == '*RAS_INT_END': break
                if data_started:
                    try:
                        parts = line.strip().split()
                        if len(parts) >= 2: angles.append(float(parts[0])); intensities.append(float(parts[1]))
                    except (ValueError, IndexError): continue
    except Exception: return None, None
    return np.array(angles, dtype=float), np.array(intensities, dtype=float)

def subtract_background(intensities: np.ndarray, window_size: int = 50) -> np.ndarray:
    """
    SNIP (simple nonlinear iterative peak-clipping) アルゴリズムに基づいてバックグラウンドを推定し、差し引く。
    Scipyのminimum_filter1dを使用して効率的に実装。
    """
    if window_size <= 0:
        return intensities
        
    # SNIPアルゴリズムは、異なるウィンドウサイズで複数回フィルタリングを適用する
    # ここでは簡略化し、指定されたウィンドウサイズで1回適用する
    background = minimum_filter1d(intensities, size=window_size)
    corrected_intensities = intensities - background
    corrected_intensities[corrected_intensities < 0] = 0
    return corrected_intensities

def _find_and_draw_peaks(ax: plt.Axes, angles: np.ndarray, intensities: np.ndarray, ymax: float, settings: Dict[str, Any]):
    if not settings.get('enabled', False):
        return

    min_height = settings.get('min_height', 0)
    min_prominence = settings.get('min_prominence', 0)
    min_width = settings.get('min_width', 0)

    # ピーク検出
    peaks, properties = find_peaks(intensities, height=min_height, prominence=min_prominence, width=min_width)

    if peaks.size > 0:
        peak_angles = angles[peaks]
        peak_intensities = properties['peak_heights']
        for angle, intensity in zip(peak_angles, peak_intensities):
            # ピーク位置にテキストを追加
            ax.text(angle, intensity, f"{angle:.1f}°", verticalalignment='bottom', horizontalalignment='center', color='purple', fontsize=8, fontweight='bold')


def _draw_reference_peaks(ax: plt.Axes, peaks_to_plot: List[Dict[str, Any]], ymax: float, appearance: Dict[str, Any]):
    if not peaks_to_plot: return
    for peak in peaks_to_plot:
        if not peak.get('visible', False): continue
        name, angle = peak.get('name', ''), peak.get('angle')
        color, linestyle = peak.get('color', 'black'), peak.get('linestyle', '--')
        if angle is not None:
            ax.axvline(x=angle, color=color, linestyle=linestyle, linewidth=1.2, ymax=1.0)
            peak_fontsize = appearance.get('peak_label_fontsize', 9)
            offset = appearance.get('peak_label_offset', 0.4)
            ax.text(angle + offset, ymax * 0.9, name, rotation=90, verticalalignment='top', 
                    horizontalalignment='left', color=color, fontsize=peak_fontsize, fontweight='bold')

def draw_plot(
    ax: plt.Axes, plot_data_full: List[Dict[str, Any]], threshold: float, x_range: Tuple[Optional[float], Optional[float]],
    reference_peaks: List[Dict[str, Any]], show_legend: bool, stack: bool, spacing: float, appearance: Dict[str, Any],
    bg_subtract_settings: Optional[Dict[str, Any]] = None,
    peak_detection_settings: Optional[Dict[str, Any]] = None,
    legend_position: Optional[Tuple[float, float]] = None
) -> Optional[str]:
    ax.clear()
    
    linewidth = appearance.get('linewidth', 1.0)
    legend_fontsize = appearance.get('legend_fontsize', 10)
    ytop_padding_factor = appearance.get('ytop_padding_factor', 1.5)
    threshold_handling = appearance.get('threshold_handling', 'hide') # 'hide' or 'clip'

    color_sequence = ['red', '#001aff', '#32CD32', '#FF8C00', '#9400D3', '#00CED1', '#FF1493', '#1E90FF', '#FFD700', '#ADFF2F']

    all_plot_points_y = []
    current_multiplier_factor = (10**spacing) # 各プロット間での乗算係数

    processed_data = []

    # ステップ0: バックグラウンド補正と閾値処理を適用
    for item in plot_data_full:
        angles = item['angles']
        intensities = np.array(item['intensities'], dtype=float)

        # バックグラウンド補正
        if bg_subtract_settings and bg_subtract_settings.get('enabled', False):
            window = bg_subtract_settings.get('window_size', 50)
            intensities = subtract_background(intensities, window)

        processed_data.append({'label': item['label'], 'angles': angles, 'intensities': intensities})


    # ステップ1: 全てのプロット対象データからY値を収集し、Y軸の範囲を決定する
    first_plot_lowest_y_val = None
    for idx, item in enumerate(processed_data):
        intensities_np = item['intensities']
        # 閾値より大きいデータのみを範囲計算の対象とする
        valid_intensities = intensities_np[intensities_np >= threshold]
        
        if valid_intensities.size == 0:
            continue

        if stack:
            current_multiplier = (current_multiplier_factor ** idx)
            plot_intensities = valid_intensities * current_multiplier
            if idx == 0:
                with np.errstate(all='ignore'):
                    first_plot_lowest_y_val = np.nanmin(plot_intensities)
        else:
            plot_intensities = valid_intensities
        
        all_plot_points_y.extend(plot_intensities)

    # ステップ2: Y軸の範囲を計算
    if not all_plot_points_y or np.all(np.isnan(all_plot_points_y)):
        ymin_val, ymax_val = 1, 10
    else:
        with np.errstate(all='ignore'):
            min_all_y = np.nanmin(all_plot_points_y)
            ymax_val = np.nanmax(all_plot_points_y) * ytop_padding_factor
        if stack and first_plot_lowest_y_val is not None and not np.isnan(first_plot_lowest_y_val):
            ymin_val = first_plot_lowest_y_val
        else:
            ymin_val = min_all_y
    
    # ステップ3: データをプロットする。この際に閾値処理を適用する
    for idx, item in enumerate(processed_data):
        angles = item['angles']
        intensities_np = item['intensities']
        
        if threshold_handling == 'hide':
            intensities_np[(intensities_np < threshold) | (intensities_np <= 0)] = np.nan
        elif threshold_handling == 'clip':
            # 閾値より小さい値をクリップする。スタック表示の場合、スケーリング前の最小値だと問題があるので、
            # 閾値自体にクリップするのが素直。
            clip_val = threshold if threshold > 0 else ymin_val 
            intensities_np[intensities_np < threshold] = clip_val
            intensities_np[intensities_np <= 0] = clip_val

        if np.all(np.isnan(intensities_np)): continue

        current_color = color_sequence[idx % len(color_sequence)]
        
        # ピーク検出はスタック表示のスケーリング前に実施
        if peak_detection_settings and peak_detection_settings.get('enabled', False) and not stack:
             _find_and_draw_peaks(ax, angles, intensities_np, ymax_val, peak_detection_settings)

        if stack:
            current_multiplier = (current_multiplier_factor ** idx)
            intensities_np = intensities_np * current_multiplier
            if peak_detection_settings and peak_detection_settings.get('enabled', False):
                 # スタック表示の場合、スケーリング後の強度でピーク検出
                 scaled_settings = peak_detection_settings.copy()
                 scaled_settings['min_height'] = scaled_settings.get('min_height', 0) * current_multiplier
                 _find_and_draw_peaks(ax, angles, intensities_np, ymax_val, scaled_settings)

        
        ax.plot(angles, intensities_np, label=item['label'], linewidth=linewidth, color=current_color)

    ax.set_ylim(bottom=ymin_val, top=ymax_val)

    ax.set_xlabel(appearance.get('xlabel', '2θ/ω (degree)'), fontsize=appearance.get('axis_label_fontsize', 20))
    ax.set_ylabel(appearance.get('ylabel', 'Log Intensity (arb. Units)'), fontsize=appearance.get('axis_label_fontsize', 20))
    
    ax.tick_params(axis='x', which='major', direction=appearance.get('tick_direction', 'in'), labelsize=appearance.get('tick_label_fontsize', 16), top=True, labeltop=False)
    ax.tick_params(axis='x', labelbottom=not appearance.get('hide_major_xtick_labels', False))

    ax.set_xlim(x_range[0], x_range[1])
    ax.set_yscale('log')
    ax.xaxis.set_major_locator(MultipleLocator(appearance.get('xaxis_major_tick_spacing', 10)))
    
    if appearance.get('show_minor_xticks', False):
        ax.xaxis.set_minor_locator(MultipleLocator(appearance.get('xminor_tick_spacing', 1.0)))
        ax.tick_params(axis='x', which='minor', direction=appearance.get('tick_direction', 'in'), bottom=True, top=True)
    else:
        ax.xaxis.set_minor_locator(NullLocator())

    # Y軸の目盛りを非表示にする
    ax.yaxis.set_major_locator(NullLocator())
    ax.yaxis.set_minor_locator(NullLocator())

    if appearance.get('show_grid', False):
        ax.grid(True, axis='x', which="both", ls="--", linewidth=0.5)
    else:
        ax.grid(False)
    
    if show_legend:
        if legend_position:
            ax.legend(fontsize=legend_fontsize, loc='lower left', bbox_to_anchor=legend_position)
        else:
            leg = ax.legend(fontsize=legend_fontsize)
            if leg: leg.set_draggable(True)

    _draw_reference_peaks(ax, reference_peaks, ymax=ax.get_ylim()[1], appearance=appearance)

    return None
