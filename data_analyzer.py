import os
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, NullLocator
import numpy as np
from typing import List, Tuple, Dict, Optional, Any

def parse_ras_file(filepath: str) -> Tuple[Optional[List[float]], Optional[List[float]]]:
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
    return angles, intensities

def _draw_reference_peaks(ax: plt.Axes, peaks_to_plot: List[Dict[str, Any]], ymax: float, appearance: Dict[str, Any]):
    if not peaks_to_plot: return
    for peak in peaks_to_plot:
        if not peak.get('visible', False): continue
        name, angle = peak.get('name', ''), peak.get('angle')
        color, linestyle = peak.get('color', 'black'), peak.get('linestyle', '--')
        if angle is not None:
            ax.axvline(x=angle, color=color, linestyle=linestyle, linewidth=1.2, ymax=0.95)
            ax.text(angle + 0.2, ymax * 0.9, name, rotation=90, verticalalignment='top', 
                    horizontalalignment='left', color=color, fontsize=appearance.get('tick_label_fontsize', 10), fontweight='bold')

def draw_plot(
    ax: plt.Axes, plot_data: List[Dict[str, str]], threshold: float, x_range: Tuple[Optional[float], Optional[float]],
    reference_peaks: List[Dict[str, Any]], show_legend: bool, stack: bool, spacing: float, appearance: Dict[str, Any]
) -> Optional[str]:
    ax.clear()
    parse_errors = []
    
    linewidth = appearance.get('linewidth', 1.0)
    legend_fontsize = appearance.get('legend_fontsize', 10)

    # --- データプロット ---
    all_plot_points_y = []
    first_plot_lowest_y_val = None

    plot_func = lambda angles, intensities, label: ax.plot(angles, intensities, label=label, linewidth=linewidth)

    if stack:
        current_multiplier = 1.0
        for idx, item in enumerate(plot_data):
            filepath = item['filepath']
            angles, intensities = parse_ras_file(filepath)
            if angles is None: parse_errors.append(os.path.basename(filepath)); continue
            
            intensities_np = np.array(intensities, dtype=float)
            intensities_np[(intensities_np < threshold) | (intensities_np <= 0)] = np.nan
            
            if np.all(np.isnan(intensities_np)): continue

            plot_intensities = intensities_np * current_multiplier
            plot_func(angles, plot_intensities, item['label'])
            all_plot_points_y.extend(plot_intensities)
            
            if idx == 0:
                with np.errstate(all='ignore'):
                    first_plot_lowest_y_val = np.nanmin(plot_intensities)

            current_multiplier *= (10**spacing)
    else: # 重ね描きモード
        for item in plot_data:
            filepath = item['filepath']
            angles, intensities = parse_ras_file(filepath)
            if angles is None: parse_errors.append(os.path.basename(filepath)); continue
            
            intensities_np = np.array(intensities, dtype=float)
            intensities_np[(intensities_np < threshold) | (intensities_np <= 0)] = np.nan
            
            if np.all(np.isnan(intensities_np)): continue

            plot_func(angles, intensities_np, item['label'])
            all_plot_points_y.extend(intensities_np)
        
    if parse_errors: return f"以下のファイルの読み込みに失敗しました:\n" + "\n".join(parse_errors)

    # --- Y軸の範囲設定 ---
    if not all_plot_points_y or np.all(np.isnan(all_plot_points_y)):
        initial_bottom_limit = threshold if threshold > 0 else 1
        ymin_val, ymax_val = initial_bottom_limit, initial_bottom_limit * 10
    else:
        with np.errstate(all='ignore'):
            min_all_y = np.nanmin(all_plot_points_y)
            ymax_val = np.nanmax(all_plot_points_y) * 1.1

        if stack and first_plot_lowest_y_val is not None and not np.isnan(first_plot_lowest_y_val):
            ymin_val = first_plot_lowest_y_val
        else:
            ymin_val = min_all_y
    
    ax.set_ylim(bottom=ymin_val, top=ymax_val)

    # --- 外観設定 ---
    ax.set_xlabel(appearance.get('xlabel', '2θ/ω (degree)'), fontsize=appearance.get('axis_label_fontsize', 20))
    ax.set_ylabel(appearance.get('ylabel', 'Log Intensity (arb. Units)'), fontsize=appearance.get('axis_label_fontsize', 20))
    ax.tick_params(axis='x', direction=appearance.get('tick_direction', 'in'), labelsize=appearance.get('tick_label_fontsize', 16))
    
    # --- 軸設定 ---
    ax.set_xlim(x_range[0], x_range[1])
    ax.set_yscale('log')
    ax.xaxis.set_major_locator(MultipleLocator(appearance.get('xaxis_major_tick_spacing', 10)))
    
    # Y軸の目盛りを完全に非表示にする
    ax.yaxis.set_major_locator(NullLocator())
    ax.yaxis.set_minor_locator(NullLocator())

    if appearance.get('show_grid', False):
        ax.grid(True, axis='x', which="both", ls="--", linewidth=0.5)
    else:
        ax.grid(False)
    
    if show_legend:
        leg = ax.legend(fontsize=legend_fontsize)
        if leg: leg.set_draggable(True)

    # --- 参照ピーク描画 ---
    _draw_reference_peaks(ax, reference_peaks, ymax=ax.get_ylim()[1], appearance=appearance)

    return None
