import os
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
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
    all_intensities = [threshold if threshold > 0 else 1]
    if stack:
        current_multiplier = 1.0
        for item in plot_data:
            filepath = item['filepath']
            angles, intensities = parse_ras_file(filepath)
            if angles is None: parse_errors.append(os.path.basename(filepath)); continue
            filtered_data = [(a, i) for a, i in zip(angles, intensities) if i >= threshold and i > 0]
            if not filtered_data: continue
            angles, intensities = zip(*filtered_data)
            plot_intensities = [i * current_multiplier for i in intensities]
            ax.plot(angles, plot_intensities, label=item['label'], linewidth=linewidth)
            all_intensities.extend(plot_intensities)
            current_multiplier *= (10**spacing)
    else:
        for item in plot_data:
            filepath = item['filepath']
            angles, intensities = parse_ras_file(filepath)
            if angles is None: parse_errors.append(os.path.basename(filepath)); continue
            filtered_data = [(a, i) for a, i in zip(angles, intensities) if i >= threshold and i > 0]
            if not filtered_data: continue
            angles, intensities = zip(*filtered_data)
            ax.plot(angles, intensities, label=item['label'], linewidth=linewidth)
            all_intensities.extend(intensities)
        
    if parse_errors: return f"以下のファイルの読み込みに失敗しました:\n" + "\n".join(parse_errors)

    # --- 外観設定 ---
    ax.set_xlabel(appearance.get('xlabel', '2θ/ω (degree)'), fontsize=appearance.get('axis_label_fontsize', 20))
    ax.set_ylabel(appearance.get('ylabel', 'Log Intensity (arb. Units)'), fontsize=appearance.get('axis_label_fontsize', 20))
    ax.tick_params(axis='both', direction=appearance.get('tick_direction', 'in'), labelsize=appearance.get('tick_label_fontsize', 16))
    
    # --- 軸設定 ---
    ax.set_xlim(x_range[0], x_range[1])
    ax.set_yscale('log')
    
    ax.xaxis.set_major_locator(MultipleLocator(appearance.get('xaxis_major_tick_spacing', 10)))
    
    # グリッド線はX軸のみに適用
    if appearance.get('show_grid', False): # デフォルトをFalseに変更
        ax.grid(True, axis='x', which="both", ls="--", linewidth=0.5)
    else:
        ax.grid(False) # 明示的にグリッドをオフ

    if stack:
        ax.tick_params(axis='y', labelleft=False) # Y軸の目盛りラベルを非表示
    else:
        ax.set_yticklabels([]) # 重ね描きモードでもY軸ラベルを非表示
    
    if show_legend:
        leg = ax.legend(fontsize=legend_fontsize)
        if leg: leg.set_draggable(True)

    # --- 参照ピーク描画 ---
    _draw_reference_peaks(ax, reference_peaks, ymax=ax.get_ylim()[1], appearance=appearance)

    return None