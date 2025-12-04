import os
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, NullLocator
import numpy as np
from typing import List, Tuple, Dict, Optional, Any

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
    reference_peaks: List[Dict[str, Any]], show_legend: bool, stack: bool, spacing: float, appearance: Dict[str, Any]
) -> Optional[str]:
    ax.clear()
    
    linewidth = appearance.get('linewidth', 1.0)
    legend_fontsize = appearance.get('legend_fontsize', 10)
    ytop_padding_factor = appearance.get('ytop_padding_factor', 1.5)

    color_sequence = ['red', '#001aff', '#32CD32', '#FF8C00', '#9400D3', '#00CED1', '#FF1493', '#1E90FF', '#FFD700', '#ADFF2F']

    all_plot_points_y = []
    first_plot_lowest_y_val = None

    current_multiplier_factor = (10**spacing) # 各プロット間での乗算係数

    for idx, item in enumerate(plot_data_full): # plot_data_full をループ
        angles = item['angles']
        intensities = item['intensities']
        
        # 閾値処理とNaNの適用は描画関数内で行う (キャッシュされたデータは生データ)
        intensities_np = np.array(intensities, dtype=float)
        intensities_np[(intensities_np < threshold) | (intensities_np <= 0)] = np.nan
        
        if np.all(np.isnan(intensities_np)): continue

        current_color = color_sequence[idx % len(color_sequence)] # 色をシーケンスから取得

        plot_intensities = intensities_np
        if stack:
            current_multiplier = (current_multiplier_factor ** idx) # 各プロットの乗数はspacingとidxで決定
            plot_intensities = intensities_np * current_multiplier
            
            if idx == 0:
                with np.errstate(all='ignore'): first_plot_lowest_y_val = np.nanmin(plot_intensities)

        ax.plot(angles, plot_intensities, label=item['label'], linewidth=linewidth, color=current_color)
        all_plot_points_y.extend(plot_intensities[~np.isnan(plot_intensities)]) # NaNを除いて追加
        
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
    
    ax.set_ylim(bottom=ymin_val, top=ymax_val)

    ax.set_xlabel(appearance.get('xlabel', '2θ/ω (degree)'), fontsize=appearance.get('axis_label_fontsize', 20))
    ax.set_ylabel(appearance.get('ylabel', 'Log Intensity (arb. Units)'), fontsize=appearance.get('axis_label_fontsize', 20))
    
    ax.tick_params(axis='x', which='major', direction=appearance.get('tick_direction', 'in'), labelsize=appearance.get('tick_label_fontsize', 16))
    ax.tick_params(axis='x', labelbottom=not appearance.get('hide_major_xtick_labels', False))

    ax.set_xlim(x_range[0], x_range[1])
    ax.set_yscale('log')
    ax.xaxis.set_major_locator(MultipleLocator(appearance.get('xaxis_major_tick_spacing', 10)))
    
    if appearance.get('show_minor_xticks', False):
        ax.xaxis.set_minor_locator(MultipleLocator(appearance.get('xminor_tick_spacing', 1.0)))
        ax.tick_params(axis='x', which='minor', direction=appearance.get('tick_direction', 'in'), bottom=True)
    else:
        ax.xaxis.set_minor_locator(NullLocator())

    ax.yaxis.set_major_locator(NullLocator())
    ax.yaxis.set_minor_locator(NullLocator())

    if appearance.get('show_grid', False):
        ax.grid(True, axis='x', which="both", ls="--", linewidth=0.5)
    else:
        ax.grid(False)
    
    if show_legend:
        leg = ax.legend(fontsize=legend_fontsize)
        if leg: leg.set_draggable(True)

    _draw_reference_peaks(ax, reference_peaks, ymax=ax.get_ylim()[1], appearance=appearance)

    return None