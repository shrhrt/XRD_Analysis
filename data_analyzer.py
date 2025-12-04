import os
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict, Optional, Any

def parse_ras_file(filepath: str) -> Tuple[Optional[List[float]], Optional[List[float]]]:
    """
    .ras ファイルをパースして、角度と強度のリストを返す。
    """
    angles, intensities = [], []
    data_started = False
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.strip() == '*RAS_INT_START':
                    data_started = True
                    continue
                if line.strip() == '*RAS_INT_END':
                    break
                if data_started:
                    try:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            angles.append(float(parts[0]))
                            intensities.append(float(parts[1]))
                    except (ValueError, IndexError):
                        continue
    except Exception:
        return None, None
    return angles, intensities

def _draw_reference_peaks(ax: plt.Axes, peaks_to_plot: List[Dict[str, Any]], ymax: float):
    """
    指定された軸に参照ピークの垂直線とラベルを描画する。
    """
    if not peaks_to_plot:
        return

    for peak in peaks_to_plot:
        if not peak.get('visible', False):
            continue

        name, angle = peak.get('name', ''), peak.get('angle')
        color, linestyle = peak.get('color', 'black'), peak.get('linestyle', '--')

        if angle is not None:
            ax.axvline(x=angle, color=color, linestyle=linestyle, linewidth=1.2, ymax=0.95)
            ax.text(angle + 0.2, ymax * 0.95, name, rotation=90, verticalalignment='top', 
                    horizontalalignment='left', color=color, fontsize=10, fontweight='bold')

def draw_plot(
    ax: plt.Axes,
    plot_data: List[Dict[str, str]],
    threshold: float,
    x_range: Tuple[Optional[float], Optional[float]],
    reference_peaks: List[Dict[str, Any]],
    show_legend: bool,
    stack: bool,
    spacing: float
) -> Optional[str]:
    """
    指定されたAxesにXRDデータを描画する。重ね描きとスタック表示（対数スケール）を切り替える。
    """
    ax.clear()
    parse_errors = []
    
    # --- データプロット ---
    if stack:
        current_multiplier = 1.0
        min_intensity = 1 # Logスケールのベースライン
        all_intensities = [min_intensity]

        for item in plot_data:
            filepath = item['filepath']
            angles, intensities = parse_ras_file(filepath)
            if angles is None or intensities is None:
                parse_errors.append(os.path.basename(filepath))
                continue
            
            # 強度がしきい値より大きく、かつ正の値のみを対象
            filtered_data = [(a, inten) for a, inten in zip(angles, intensities) if inten >= threshold and inten > 0]
            if not filtered_data: continue

            angles, intensities = zip(*filtered_data)
            
            plot_intensities = [i * current_multiplier for i in intensities]
            
            ax.plot(angles, plot_intensities, label=item['label'])
            all_intensities.extend(plot_intensities)
            
            current_multiplier *= (10**spacing) # spacingは10のべき乗として扱う

        ax.set_yscale('log')

    else: # 重ね描きモード
        all_intensities = [threshold if threshold > 0 else 1]
        for item in plot_data:
            filepath = item['filepath']
            angles, intensities = parse_ras_file(filepath)
            if angles is None or intensities is None:
                parse_errors.append(os.path.basename(filepath))
                continue

            filtered_data = [(a, inten) for a, inten in zip(angles, intensities) if inten >= threshold and inten > 0]
            if not filtered_data: continue

            angles, intensities = zip(*filtered_data)
            ax.plot(angles, intensities, label=item['label'])
            all_intensities.extend(intensities)
        
        ax.set_yscale('log')

    if parse_errors:
        return f"以下のファイルの読み込みに失敗しました:\n" + "\n".join(parse_errors)

    # --- 軸の設 ---
    ax.set_xlim(x_range[0], x_range[1])
    ax.set_xlabel("2θ/ω (degree)")
    ax.grid(True, which="both", ls="--", linewidth=0.5, axis='x')
    
    if stack:
        ax.set_yticks([])
        ax.set_yticklabels([])
        ax.set_ylabel("Log Intensity (arb. Units)") # Y軸ラベルを表示
        ax.set_ylim(bottom=min(all_intensities)*0.9, top=max(all_intensities) * 1.5)
        if show_legend: # スタックモードでも凡例を表示
            leg = ax.legend(loc='upper right', bbox_to_anchor=(1.0, 1.0)) # 凡例位置を調整
            if leg:
                leg.set_draggable(True)
    else:
        ax.set_ylabel("Log Intensity (arb. Units)")
        ax.set_ylim(bottom=min(all_intensities), top=max(all_intensities) * 1.5)
        ax.yaxis.grid(False)
        ax.set_yticklabels([])
        if show_legend:
            leg = ax.legend()
            if leg:
                leg.set_draggable(True)

    # --- 参照ピーク描画 ---
    _draw_reference_peaks(ax, reference_peaks, ymax=ax.get_ylim()[1])

    return None