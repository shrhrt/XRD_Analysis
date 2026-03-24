import numpy as np
import os
import pytest
import math

# テスト対象の関数をインポート
from data_analyzer import parse_ras_file, calculate_d_value, calculate_lattice_constant


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
