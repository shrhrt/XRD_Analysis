import os
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict, Optional, Any

def parse_ras_file(filepath: str) -> Tuple[Optional[List[float]], Optional[List[float]]]:
    """
    .ras ファイルをパースして、角度と強度のリストを返す。
    エラーが発生した場合は (None, None) を返す。
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

def _draw_reference_peaks(ax: plt.Axes, peaks_to_plot: List[Dict[str, Any]]):
    """
    指定された軸に参照ピークの垂直線とラベルを描画する。
    """
    if not peaks_to_plot:
        return

    ymin, ymax = ax.get_ylim()

    unique_names = sorted(list(set([p['name'] for p in peaks_to_plot])))
    dark_colors = ['#8B0000', '#00008B', '#006400', '#8B008B', '#FF8C00', '#483D8B', '#B22222', '#008B8B', '#556B2F', '#9932CC']
    color_map = {name: dark_colors[i % len(dark_colors)] for i, name in enumerate(unique_names)}

    for peak in peaks_to_plot:
        name, angle = peak['name'], peak['angle']
        color = color_map[name]
        ax.axvline(x=angle, color=color, linestyle='--', linewidth=1.2)
        y_pos = ymax * 0.95
        ax.text(angle + 0.2, y_pos, name, rotation=90, verticalalignment='top', horizontalalignment='left', color=color, fontsize=10, fontweight='bold')

def create_plot_figure(
    filepaths: List[str],
    threshold: float,
    x_range: Tuple[Optional[float], Optional[float]],
    reference_peaks: List[Dict[str, Any]]
) -> Tuple[Optional[plt.Figure], Optional[str]]:
    """
    XRDデータからmatplotlibのFigureオブジェクトを生成する。

    Returns:
        Tuple[Optional[plt.Figure], Optional[str]]: 成功時は(Figure, None)、
                                                   失敗時は(None, エラーメッセージ)を返す。
    """
    fig, ax = plt.subplots(figsize=(16, 9))
    has_data_to_plot = False
    parse_errors = []

    for filepath in filepaths:
        angles, intensities = parse_ras_file(filepath)
        if angles is None or intensities is None:
            parse_errors.append(filepath)
            continue

        filtered_data = [(a, inten) for a, inten in zip(angles, intensities) if inten >= threshold]
        if not filtered_data:
            continue

        has_data_to_plot = True
        angles, intensities = zip(*filtered_data)
        ax.plot(angles, intensities, label=os.path.basename(filepath))

    if parse_errors:
        error_files = "\n".join(parse_errors)
        plt.close(fig)
        return None, f"以下のファイルの読み込みに失敗しました:\n{error_files}"

    if not has_data_to_plot:
        plt.close(fig)
        return None, f"表示するデータがありません。\n(強度しきい値: {threshold})"

    ax.set_xlabel("2θ/ω (degree)")
    ax.set_ylabel("Log Intensity (a.u.)")
    ax.set_yscale('log')
    ax.set_ylim(bottom=threshold if threshold > 0 else 1)

    _draw_reference_peaks(ax, reference_peaks)

    xmin, xmax = x_range
    ax.set_xlim(xmin, xmax)

    ax.legend()
    ax.grid(True, which="both", ls="--", linewidth=0.5, axis='x')
    ax.yaxis.grid(False)
    ax.set_yticklabels([])
    fig.tight_layout()

    return fig, None

def draw_plot_on_axes(
    ax: plt.Axes,
    filepaths: List[str],
    threshold: float,
    x_range: Tuple[Optional[float], Optional[float]],
    reference_peaks: List[Dict[str, Any]]
) -> Optional[str]:
    """
    指定されたmatplotlibのAxesにXRDデータを描画する。

    Returns:
        Optional[str]: 失敗時にエラーメッセージを返す。
    """
    ax.clear()
    has_data_to_plot = False
    parse_errors = []

    for filepath in filepaths:
        angles, intensities = parse_ras_file(filepath)
        if angles is None or intensities is None:
            parse_errors.append(filepath)
            continue

        filtered_data = [(a, inten) for a, inten in zip(angles, intensities) if inten >= threshold]
        if not filtered_data:
            continue

        has_data_to_plot = True
        angles, intensities = zip(*filtered_data)
        ax.plot(angles, intensities, label=os.path.basename(filepath))

    if parse_errors:
        return f"以下のファイルの読み込みに失敗しました:\n" + "\n".join(parse_errors)

    ax.set_xlabel("2θ/ω (degree)")
    ax.set_ylabel("Log Intensity (a.u.)")
    ax.set_yscale('log')
    ax.set_ylim(bottom=threshold if threshold > 0 else 1)
    _draw_reference_peaks(ax, reference_peaks)
    ax.set_xlim(x_range[0], x_range[1])
    ax.legend()
    ax.grid(True, which="both", ls="--", linewidth=0.5, axis='x')
    ax.yaxis.grid(False)
    ax.set_yticklabels([])
    return None