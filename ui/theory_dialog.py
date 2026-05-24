import tkinter as tk
from tkinter import ttk


def show_theory_dialog(master):
    """理論・計算式の解説ウィンドウを開く"""
    win = tk.Toplevel(master)
    win.title("理論・計算式の解説")
    win.geometry("720x580")
    win.resizable(True, True)

    nb = ttk.Notebook(win)
    nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    for title, builder in [
        ("ブラッグの法則",    _bragg_content),
        ("格子定数 (立方晶)", _lattice_content),
        ("Gaussian フィット", _gaussian_content),
        ("シェラー式",        _scherrer_content),
    ]:
        frame = ttk.Frame(nb)
        nb.add(frame, text=title)
        _build_text(frame, builder)


# ------------------------------------------------------------------ #
# テキストウィジェット共通構築
# ------------------------------------------------------------------ #

def _build_text(parent, builder):
    parent.rowconfigure(0, weight=1)
    parent.columnconfigure(0, weight=1)

    text = tk.Text(
        parent, wrap=tk.WORD, padx=20, pady=14,
        relief="flat", bd=0, cursor="arrow",
    )
    vsb = ttk.Scrollbar(parent, orient="vertical", command=text.yview)
    text.configure(yscrollcommand=vsb.set)
    text.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")

    # --- タグ定義 ---
    text.tag_configure("h1",
        font=("", 15, "bold"),
        foreground="#1a3a5c",
        spacing1=4, spacing3=10)

    text.tag_configure("h2",
        font=("", 11, "bold"),
        foreground="#2e6da4",
        spacing1=12, spacing3=4)

    text.tag_configure("formula",
        font=("Courier New", 11),
        foreground="#0d5c8e",
        lmargin1=28, lmargin2=28,
        spacing1=6, spacing3=6)

    text.tag_configure("body",
        font=("", 10),
        spacing1=2, spacing3=2)

    text.tag_configure("bullet",
        font=("", 10),
        lmargin1=24, lmargin2=36,
        spacing1=3)

    text.tag_configure("subbullet",
        font=("", 10),
        foreground="#555555",
        lmargin1=42, lmargin2=54,
        spacing1=2)

    text.tag_configure("label",
        font=("", 10, "bold"),
        foreground="#333333")

    text.tag_configure("note",
        font=("", 9),
        foreground="#888888",
        lmargin1=24, spacing1=2)

    builder(text)
    text.config(state="disabled")


def _i(t, s, tag="body"):
    t.insert(tk.END, s, tag)


# ------------------------------------------------------------------ #
# タブコンテンツ
# ------------------------------------------------------------------ #

def _bragg_content(t):
    _i(t, "ブラッグの法則\n", "h1")

    _i(t, "概要\n", "h2")
    _i(t, "X 線が結晶の格子面（面間隔 d の等間隔面群）で反射するとき、"
          "隣接面からの反射波の光路差が波長の整数倍になると強め合う。"
          "この条件を与えるのがブラッグの法則であり、ピーク位置 2θ を測定することで"
          "面間隔 d を直接求めることができる。\n")

    _i(t, "式\n", "h2")
    _i(t, "  nλ = 2d · sinθ\n", "formula")

    _i(t, "各記号\n", "h2")
    _i(t, "  n  ─  回折次数（通常 n = 1）\n", "bullet")
    _i(t, "  λ  ─  X 線波長  Co Kα₁ = 1.78897 Å\n", "bullet")
    _i(t, "  d  ─  結晶面間隔（d-spacing）[Å]\n", "bullet")
    _i(t, "  θ  ─  ブラッグ角（測定角 2θ の半分）\n")

    _i(t, "d の算出式（本アプリの計算）\n", "h2")
    _i(t, "  d = λ / (2·sinθ)    θ = (測定 2θ) / 2\n", "formula")

    _i(t, "高次反射について\n", "h2")
    _i(t, "  MgO の 001 面を 2 次（n=2）で測定したものは「002 反射」と表記する。\n", "bullet")
    _i(t, "  このとき d₀₀₂ = d₀₀₁ / 2 となる。\n", "bullet")
    _i(t, "  本アプリは n=1 固定。002, 004, 008 はそれぞれ独立した d として計算する。\n", "bullet")


def _lattice_content(t):
    _i(t, "格子定数計算（立方晶）\n", "h1")

    _i(t, "概要\n", "h2")
    _i(t, "立方晶系では全軸が等長（a = b = c）で直交するため、"
          "面間隔 d と格子定数 a の関係が以下の簡潔な式で表せる。"
          "ブラッグの法則で求めた d に面指数 hkl を入力すると a が計算できる。\n")

    _i(t, "立方晶の面間隔\n", "h2")
    _i(t, "  d_hkl = a / √(h² + k² + l²)\n", "formula")

    _i(t, "格子定数の計算式（本アプリの計算）\n", "h2")
    _i(t, "  a = d_hkl · √(h² + k² + l²)\n", "formula")

    _i(t, "各記号\n", "h2")
    _i(t, "  a      ─  格子定数 [Å]\n", "bullet")
    _i(t, "  d_hkl  ─  (hkl) 面の面間隔（ブラッグの法則から取得）[Å]\n", "bullet")
    _i(t, "  h, k, l  ─  ミラー指数\n")

    _i(t, "計算例\n", "h2")
    _i(t, "  MgO 002   d = 2.106 Å  →  a = 2.106 × √4  = 2.106 × 2 = 4.212 Å\n", "bullet")
    _i(t, "  Fe₃O₄ 004  d = 2.099 Å  →  a = 2.099 × √16 = 2.099 × 4 = 8.396 Å\n", "bullet")
    _i(t, "  Fe₃O₄ 008  d = 1.050 Å  →  a = 1.050 × √64 = 1.050 × 8 = 8.400 Å\n", "bullet")
    _i(t, "  004 と 008 の a がほぼ一致する → 測定精度の確認に使える。\n", "note")

    _i(t, "注意点\n", "h2")
    _i(t, "  本アプリは立方晶のみ対応。正方晶・六方晶等では異なる式が必要。\n", "bullet")
    _i(t, "  正方晶：  1/d² = (h²+k²)/a²  +  l²/c²\n", "subbullet")
    _i(t, "  六方晶：  1/d² = 4(h²+hk+k²)/(3a²)  +  l²/c²\n", "subbullet")


def _gaussian_content(t):
    _i(t, "Gaussian フィッティング\n", "h1")

    _i(t, "概要\n", "h2")
    _i(t, "XRD ピークを Gaussian 関数でフィットすることで、データ点の間隔に縛られない"
          "精密なピーク位置と FWHM を抽出する。FWHM はシェラー式の入力として使用する。\n")

    _i(t, "フィットモデル\n", "h2")
    _i(t, "  I(2θ) = A · exp[−(2θ − 2θ₀)² / (2σ²)]  +  a·2θ + b\n", "formula")

    _i(t, "各パラメータ\n", "h2")
    _i(t, "  A    ─  ピーク振幅（バックグラウンドを差し引いた最大強度）\n", "bullet")
    _i(t, "  2θ₀  ─  ピーク中心位置 [°]　← d 値・格子定数の計算に使用\n", "bullet")
    _i(t, "  σ    ─  標準偏差 [°]\n", "bullet")
    _i(t, "  a, b  ─  線形バックグラウンドの傾きと切片\n", "bullet")
    _i(t, "  a·2θ + b を同時フィットするため、背景を手動除去しなくてよい。\n", "note")

    _i(t, "FWHM（半値全幅）\n", "h2")
    _i(t, "  β = 2√(2·ln2) · σ  ≈  2.3548 · σ\n", "formula")
    _i(t, "  ピーク最大強度の 1/2 の高さにおける幅。シェラー式の β として使用。\n")

    _i(t, "フィット品質：R²（決定係数）\n", "h2")
    _i(t, "  R² = 1 − SS_res / SS_tot\n\n"
          "  SS_res = Σ(yi − ŷi)²    残差平方和\n"
          "  SS_tot = Σ(yi − ȳ)²     全平方和\n", "formula")
    _i(t, "  R² = 1.0  完全フィット  /  R² < 0.95  ピーク範囲や形状を見直す\n", "note")

    _i(t, "パラメータの不確かさ（±）\n", "h2")
    _i(t, "  σ_param = √diag(pcov)\n", "formula")
    _i(t, "  scipy の curve_fit が返す共分散行列 pcov の対角成分の平方根。\n", "bullet")
    _i(t, "  結果テーブルの「±」はこの値。\n")

    _i(t, "注意点\n", "h2")
    _i(t, "  XRD ピークの真の形状は Voigt 関数（Gaussian と Lorentzian の畳み込み）。\n", "bullet")
    _i(t, "  Gaussian は近似のため、ピーク裾野でズレが生じることがある。\n", "subbullet")
    _i(t, "  フィットは線形強度値（実測値）で実施。グラフの log 表示とは無関係。\n", "bullet")
    _i(t, "  範囲内に 5 点以上のデータ点が必要。\n", "bullet")


def _scherrer_content(t):
    _i(t, "シェラー式（結晶子サイズ）\n", "h1")

    _i(t, "概要\n", "h2")
    _i(t, "ピーク幅（FWHM）は結晶子（コヒーレントに回折するドメイン）が小さいほど広くなる。"
          "シェラー式はこの関係を利用して FWHM から結晶子サイズ D を推定する。"
          "面直測定（θ-2θ スキャン）では D は膜面垂直方向（成長方向）の秩序の長さを表す。\n")

    _i(t, "式\n", "h2")
    _i(t, "  D = K·λ / (β·cosθ)\n", "formula")

    _i(t, "各記号\n", "h2")
    _i(t, "  D  ─  結晶子サイズ [Å]\n", "bullet")
    _i(t, "  K  ─  シェラー定数 = 0.94　（球状結晶を仮定。形状により 0.89〜1.0）\n", "bullet")
    _i(t, "  λ  ─  X 線波長 = 1.78897 Å　（Co Kα₁）\n", "bullet")
    _i(t, "  β  ─  FWHM [rad]  = FWHM [°] × π / 180\n", "bullet")
    _i(t, "  θ  ─  ブラッグ角 = 2θ₀ / 2\n")

    _i(t, "誤差伝播\n", "h2")
    _i(t, "  σD = D · (σβ / β)\n", "formula")
    _i(t, "  σβ は FWHM の標準誤差（Gaussian フィットの共分散行列から取得）。\n", "bullet")
    _i(t, "  結果テーブルの D の「±」として表示される。\n")

    _i(t, "信頼性の判断（アプリ内の表示基準）\n", "h2")
    _i(t, "  ✓  R² ≥ 0.99 かつ FWHM ≥ 0.1°  →  良好\n", "bullet")
    _i(t, "  △  FWHM < 0.1°  →  装置分解能限界付近\n", "bullet")
    _i(t, "     装置広がり β_inst を差し引いていないため D を過大評価する恐れ。\n", "subbullet")
    _i(t, "     補正式：β_size = √(β_obs² − β_inst²)\n", "subbullet")
    _i(t, "  ✗  R² < 0.95  →  フィット自体が不良\n")

    _i(t, "D の値の目安（面直測定）\n", "h2")
    _i(t, "  D < 100 Å     ─  ナノ結晶・高密度欠陥や粒界\n", "bullet")
    _i(t, "  D 100〜1000 Å  ─  通常の薄膜域\n", "bullet")
    _i(t, "  D > 1000 Å    ─  装置分解能限界付近（参考値として扱う）\n")

    _i(t, "本質的な限界\n", "h2")
    _i(t, "  装置分解能補正（標準試料で β_inst を実測）を行っていない。\n", "bullet")
    _i(t, "  格子歪み（microstrain）によるブロードニングと区別できない。\n", "bullet")
    _i(t, "  分離には Williamson-Hall 法が必要（本アプリ未実装）。\n", "subbullet")
    _i(t, "  精度の目安：理想条件でも ±10〜30%。\n", "bullet")
