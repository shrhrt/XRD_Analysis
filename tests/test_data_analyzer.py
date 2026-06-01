import numpy as np
import os
import pytest
import math

# テスト対象の関数をインポート
from core.data_analyzer import (
    parse_ras_file,
    calculate_d_value,
    calculate_lattice_constant,
    _detect_peaks,
    draw_plot,
    PlotSettings,
)


def test_parse_ras_file_success(tmp_path):
    """
    正常系テスト:
    正しいフォーマットのRASファイルを読み込んだ時、
    正しく角度と強度のNumpy配列が抽出されるかを検証する。
    """
    # Arrange (準備): pytestの便利機能「tmp_path」を使って、テスト用の一時ファイルを作る
    # テストが終わると、このファイルは自動で綺麗に削除されます！
    dummy_file = tmp_path / "dummy.ras"
    dummy_content = """
*RAS_DATA_START
*RAS_INT_START
10.0 100.5
20.0 200.0
30.0 300.5
*RAS_INT_END
*RAS_DATA_END
    """
    dummy_file.write_text(dummy_content, encoding="utf-8")

    # Act (実行): テスト対象の関数にダミーファイルを渡す
    angles, intensities = parse_ras_file(str(dummy_file))

    # Assert (検証): 帰ってきた結果が期待通りかチェックする
    # 1. None ではなく、ちゃんとデータが入っているか？
    assert angles is not None
    assert intensities is not None

    # 2. データの個数は3個か？
    assert len(angles) == 3
    assert len(intensities) == 3

    # 3. 中身の数値は合っているか？
    assert np.array_equal(angles, np.array([10.0, 20.0, 30.0]))
    assert np.array_equal(intensities, np.array([100.5, 200.0, 300.5]))


def test_parse_ras_file_not_found():
    """
    異常系テスト:
    存在しないファイルを読み込もうとした時、
    アプリが落ちずに (None, None) を返すかを検証する。
    """
    angles, intensities = parse_ras_file("not_exist_file.ras")
    assert angles is None
    assert intensities is None


def test_calculate_d_value():
    """d値の計算ロジックが正しいかを検証する"""
    # 正常系: 2θ = 90度の時
    # λ = 1.78897, θ = 45度 -> sin(45°) = 1/√2
    # d = 1.78897 / (2 * (1/√2)) = 1.78897 / √2 ≒ 1.26499...
    expected_d = 1.78897 / math.sqrt(2)
    result_d = calculate_d_value(90.0)
    # 浮動小数点の計算結果は完全に一致しないことがあるため、iscloseで検証
    assert math.isclose(result_d, expected_d, rel_tol=1e-5)

    # 異常系: 0度以下や180度以上が入力されたら、ValueErrorを出す(raiseする)か検証
    with pytest.raises(ValueError):
        calculate_d_value(0.0)
    with pytest.raises(ValueError):
        calculate_d_value(180.0)


def test_calculate_lattice_constant():
    """格子定数の計算ロジックが正しいかを検証する"""
    # 正常系: d = 2.0, (h, k, l) = (1, 1, 1) の時
    # a = 2.0 * √(1^2 + 1^2 + 1^2) = 2.0 * √3 ≒ 3.4641...
    expected_a = 2.0 * math.sqrt(3)
    result_a = calculate_lattice_constant(2.0, 1, 1, 1)
    assert math.isclose(result_a, expected_a, rel_tol=1e-5)

    # 異常系: (h, k, l) が (0, 0, 0) の時
    with pytest.raises(ValueError):
        calculate_lattice_constant(2.0, 0, 0, 0)


# -----------------------------------------------------------------------
# _detect_peaks のテスト
# -----------------------------------------------------------------------

def _make_settings(height=5.0, prominence=5.0, width=0.1, trim_top=0.0):
    return {
        "enabled": True,
        "trim_top_pct": trim_top,   # 0=無効(全ピーク検出), >0=最大値の%以上を基板除外
        "min_height": height,
        "min_prominence": prominence,
        "min_width": width,
    }


def test_detect_peaks_finds_single_clear_peak():
    """明確なピークが1つあるデータを正しく検出できることを検証する"""
    # 0.1°ステップ, 100点のフラットな背景の上にピーク1本
    angles = np.linspace(30.0, 40.0, 101)       # 0.1°/点
    intensities = np.ones(101) * 100.0
    intensities[50] = 5000.0                      # 50番目に突出したピーク

    peak_angles, peak_intensities = _detect_peaks(angles, intensities, _make_settings())

    assert len(peak_angles) == 1
    assert math.isclose(peak_angles[0], angles[50], abs_tol=0.15)
    assert math.isclose(peak_intensities[0], 5000.0, rel_tol=1e-5)


def test_detect_peaks_ignores_nan_values():
    """NaN を含むデータでも安全にピーク検出でき、かつ NaN 付近を誤検出しないことを検証する"""
    angles = np.linspace(30.0, 40.0, 101)
    intensities = np.ones(101) * 100.0
    intensities[50] = 5000.0                      # 真のピーク
    intensities[10] = np.nan                      # NaN を混入
    intensities[80] = np.nan

    peak_angles, peak_intensities = _detect_peaks(angles, intensities, _make_settings())

    # NaN 境界で誤検出せず、真のピークだけ検出されること
    assert len(peak_angles) == 1
    assert math.isclose(peak_angles[0], angles[50], abs_tol=0.15)


def test_detect_peaks_does_not_modify_input():
    """_detect_peaks が入力配列を書き換えないことを検証する（バグ回帰テスト）"""
    angles = np.linspace(30.0, 40.0, 101)
    intensities = np.ones(101) * 100.0
    intensities[50] = 5000.0
    original = intensities.copy()

    _detect_peaks(angles, intensities, _make_settings())

    assert np.array_equal(intensities, original), "入力データが変更されている（バグ）"


def test_detect_peaks_disabled():
    """enabled=False のとき何も検出しないことを検証する"""
    angles = np.linspace(30.0, 40.0, 101)
    intensities = np.ones(101) * 100.0
    intensities[50] = 5000.0

    settings = _make_settings()
    settings["enabled"] = False
    peak_angles, peak_intensities = _detect_peaks(angles, intensities, settings)

    assert len(peak_angles) == 0


def test_detect_peaks_high_threshold_rejects_small_peaks():
    """height/prominence の閾値を高くすると小さいピークが除外されることを検証する"""
    angles = np.linspace(30.0, 40.0, 101)
    intensities = np.ones(101) * 100.0
    intensities[20] = 150.0    # 小さいピーク (薄膜 max の 15%)
    intensities[50] = 1000.0   # 大きい薄膜ピーク
    intensities[80] = 5000.0   # 基板ピーク (global max)

    # trim_top=30% → 基板閾値 = 30% × 5000 = 1500 → 基板(5000)除外
    # 除外後の data_max = 1000
    # height=20% → effective_height=200 → 小ピーク(150)<200 → 除外
    # 大ピーク(1000) > 200 → 検出
    peak_angles, _ = _detect_peaks(
        angles, intensities, _make_settings(height=20.0, prominence=20.0, trim_top=30.0)
    )

    assert len(peak_angles) == 1
    assert math.isclose(peak_angles[0], angles[50], abs_tol=0.15)


def test_detect_peaks_width_filters_narrow_spike():
    """width を大きくすると幅の狭いスパイクが除外されることを検証する"""
    # 0.02°/点（XRD の典型的なステップ）
    angles = np.linspace(30.0, 50.0, 1001)       # 0.02°/点
    intensities = np.ones(1001) * 100.0
    intensities[500] = 5000.0                     # 1点だけのスパイク（幅 ≈ 0.02°）
    # 本物のブロードなピーク（sigma=15点=0.3°、FWHM≈0.7°）
    for i in range(650, 776):
        intensities[i] = 100.0 + 4900.0 * np.exp(-0.5 * ((i - 712) / 15) ** 2)

    # width=0.3° → スパイク(0.02°)は除外、ブロードピーク(0.5°)は通過
    peak_angles, _ = _detect_peaks(
        angles, intensities, _make_settings(height=5.0, prominence=5.0, width=0.3)
    )

    spike_angle = angles[500]
    assert not any(math.isclose(a, spike_angle, abs_tol=0.05) for a in peak_angles), \
        "幅の狭いスパイクが誤検出されている"
    assert len(peak_angles) >= 1, "ブロードなピークが検出されていない"


def test_draw_plot_does_not_mutate_parsed_data():
    """draw_plot を呼んでも parsed_data の元データが書き換わらないことを検証する（バグ回帰テスト）"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    angles = np.linspace(30.0, 130.0, 1001)
    intensities = np.abs(np.random.default_rng(0).normal(500, 50, 1001)) + 1.0
    original = intensities.copy()

    plot_data = [{"label": "test", "angles": angles, "intensities": intensities}]
    settings = PlotSettings(
        threshold=10.0,
        x_range=(30.0, 130.0),
        show_legend=False,
        stack=False,
        spacing=3.0,
        appearance={
            "threshold_handling": "hide",
            "yscale": "log",
            "linewidth": 1.0,
            "legend_fontsize": 10,
            "ytop_padding_factor": 1.5,
            "font_family": "sans-serif",
            "xlabel": "2θ",
            "ylabel": "Intensity",
            "axis_label_fontsize": 14,
            "tick_label_fontsize": 12,
            "tick_direction": "in",
            "xaxis_major_tick_spacing": 10,
            "show_grid": False,
            "hide_major_xtick_labels": False,
            "show_minor_xticks": False,
            "xminor_tick_spacing": 1.0,
            "peak_label_fontsize": 9,
            "peak_label_offset": 0.4,
            "peak_label_y": 0.9,
            "match_math_font": False,
            "legend_loc": "best",
            "legend_frame": True,
            "legend_bgcolor": "white",
            "legend_italic": False,
        },
    )

    fig, ax = plt.subplots()
    draw_plot(ax, plot_data, settings)
    plt.close(fig)

    assert np.array_equal(intensities, original), "draw_plot が元データを書き換えた（バグ）"
