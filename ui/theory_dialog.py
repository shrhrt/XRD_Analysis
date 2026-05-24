import tkinter as tk
from tkinter import ttk


def show_theory_dialog(master):
    """理論・計算式の解説ウィンドウを開く（既に開いていれば前面に出す）"""
    win = tk.Toplevel(master)
    win.title("理論・計算式の解説")
    win.geometry("700x560")
    win.resizable(True, True)

    nb = ttk.Notebook(win)
    nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    sections = [
        ("ブラッグの法則",    _bragg_content),
        ("格子定数 (立方晶)", _lattice_content),
        ("Gaussian フィット", _gaussian_content),
        ("シェラー式",        _scherrer_content),
    ]
    for title, builder in sections:
        frame = ttk.Frame(nb)
        nb.add(frame, text=title)
        _build_text(frame, builder)


# ------------------------------------------------------------------ #
# テキストウィジェット共通構築
# ------------------------------------------------------------------ #

def _build_text(parent, builder):
    parent.rowconfigure(0, weight=1)
    parent.columnconfigure(0, weight=1)

    bg = ttk.Style().lookup("TFrame", "background") or "#ffffff"
    fg = ttk.Style().lookup("TLabel", "foreground") or "#000000"
    formula_bg = "#e8eef4" if bg.startswith("#f") or bg == "#ffffff" else "#2a3040"

    text = tk.Text(
        parent, wrap=tk.WORD, padx=18, pady=12,
        font=("", 10), relief="flat", bd=0,
        background=bg, foreground=fg,
        selectbackground="#4a90d9", selectforeground="white",
    )
    vsb = ttk.Scrollbar(parent, orient="vertical", command=text.yview)
    text.configure(yscrollcommand=vsb.set)
    text.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")

    text.tag_configure("h1",      font=("", 14, "bold"), spacing1=10, spacing3=6)
    text.tag_configure("h2",      font=("", 11, "bold"), spacing1=8,  spacing3=3,
                       foreground="#1a5276" if fg == "#000000" else "#82c4f5")
    text.tag_configure("formula", font=("Courier New", 10),
                       background=formula_bg,
                       lmargin1=24, lmargin2=24, spacing1=6, spacing3=6)
    text.tag_configure("body",   font=("", 10), spacing1=3)
    text.tag_configure("bullet", font=("", 10), lmargin1=22, lmargin2=34, spacing1=2)
    text.tag_configure("subbullet", font=("", 10), lmargin1=38, lmargin2=50,
                       spacing1=1, foreground="#555555" if fg == "#000000" else "#aaaaaa")
    text.tag_configure("note",   font=("", 9),  foreground="#777777", spacing1=2,
                       lmargin1=10)

    builder(text)
    text.config(state="disabled")


def _ins(t, s, tag="body"):
    t.insert(tk.END, s, tag)


# ------------------------------------------------------------------ #
# 各タブのコンテンツ
# ------------------------------------------------------------------ #

def _bragg_content(t):
    _ins(t, "ブラッグの法則\n", "h1")

    _ins(t, "概要\n", "h2")
    _ins(t, "X 線が結晶の格子面（間隔 d の等間隔面群）で反射するとき、"
           "隣接面からの反射波の光路差が波長の整数倍になれば強め合う。"
           "この条件がブラッグの法則であり、ピーク位置 2θ を測定することで"
           "面間隔 d を直接求めることができる。\n\n", "body")

    _ins(t, "式\n", "h2")
    _ins(t, "    nλ = 2d · sin(θ)\n\n", "formula")

    _ins(t, "各記号\n", "h2")
    _ins(t, "  n   : 回折次数（通常 n = 1。002, 004 等の高指数表記では n を吸収済み）\n", "bullet")
    _ins(t, "  λ   : X 線波長　→ Co Kα1 = 1.78897 Å\n", "bullet")
    _ins(t, "  d   : 結晶面間隔 d-spacing　[Å]\n", "bullet")
    _ins(t, "  θ   : ブラッグ角（2θ の半分）\n\n", "bullet")

    _ins(t, "d の算出式（本アプリの計算）\n", "h2")
    _ins(t, "    d = λ / (2 · sin(θ))    where θ = (2θ_measured) / 2\n\n", "formula")

    _ins(t, "高次反射について\n", "h2")
    _ins(t, "  MgO の 001 面（n=2）は「002 反射」として表記し、d_002 = d_001 / 2 となる。\n", "bullet")
    _ins(t, "  本アプリは n=1 固定で計算する。002, 004, 008 はそれぞれ独立した d として扱う。\n\n", "bullet")


def _lattice_content(t):
    _ins(t, "格子定数計算（立方晶）\n", "h1")

    _ins(t, "概要\n", "h2")
    _ins(t, "立方晶系では全軸が等長（a = b = c）で直交するため、"
           "面間隔 d と格子定数 a の関係が簡単な式で表せる。"
           "ブラッグの法則で求めた d に面指数 hkl を与えると a が計算できる。\n\n", "body")

    _ins(t, "立方晶の面間隔\n", "h2")
    _ins(t, "    1/d² = (h² + k² + l²) / a²\n\n"
           "    → d_hkl = a / sqrt(h² + k² + l²)\n\n", "formula")

    _ins(t, "格子定数の計算式\n", "h2")
    _ins(t, "    a = d_hkl · sqrt(h² + k² + l²)\n\n", "formula")

    _ins(t, "各記号\n", "h2")
    _ins(t, "  a      : 格子定数　[Å]\n", "bullet")
    _ins(t, "  d_hkl  : (hkl) 面の面間隔（ブラッグの法則から取得）　[Å]\n", "bullet")
    _ins(t, "  h, k, l: ミラー指数\n\n", "bullet")

    _ins(t, "計算例\n", "h2")
    _ins(t, "  MgO 002  (d ≈ 2.106 Å) → a = 2.106 × sqrt(4)  = 2.106 × 2 = 4.212 Å\n", "bullet")
    _ins(t, "  Fe₃O₄ 004 (d ≈ 2.099 Å) → a = 2.099 × sqrt(16) = 2.099 × 4 = 8.396 Å\n", "bullet")
    _ins(t, "  Fe₃O₄ 008 (d ≈ 1.050 Å) → a = 1.050 × sqrt(64) = 1.050 × 8 = 8.400 Å\n\n", "bullet")
    _ins(t, "  004 と 008 は同じ物質なので a がほぼ一致する。\n"
           "  複数の反射で a を比較することで測定精度を確認できる。\n\n", "subbullet")

    _ins(t, "注意点\n", "h2")
    _ins(t, "  ・本アプリは立方晶（cubic）のみ対応。\n", "bullet")
    _ins(t, "  ・正方晶（a≠c）: 1/d² = (h²+k²)/a² + l²/c²\n", "bullet")
    _ins(t, "  ・六方晶       : 1/d² = 4(h²+hk+k²)/(3a²) + l²/c²\n", "bullet")


def _gaussian_content(t):
    _ins(t, "Gaussian フィッティング\n", "h1")

    _ins(t, "概要\n", "h2")
    _ins(t, "XRD ピークを Gaussian 関数でフィットすることで、測定データ点の間隔に縛られない"
           "精密なピーク位置・FWHM・強度を抽出する。"
           "これによりシェラー式への入力となる FWHM が得られる。\n\n", "body")

    _ins(t, "フィットモデル\n", "h2")
    _ins(t, "    I(2θ) = A · exp( -(2θ - 2θ₀)² / (2σ²) ) + a·2θ + b\n\n", "formula")
    _ins(t, "  A    : ピーク振幅（バックグラウンドを差し引いた最大強度）\n", "bullet")
    _ins(t, "  2θ₀  : ピーク中心位置　[°]　← 格子定数・d 値の計算に使用\n", "bullet")
    _ins(t, "  σ    : 標準偏差　[°]\n", "bullet")
    _ins(t, "  a, b : 線形バックグラウンドの傾きと切片\n\n", "bullet")
    _ins(t, "  バックグラウンドを線形項で同時フィットすることで、\n"
           "  背景を手動で除去しなくてもよい。\n\n", "subbullet")

    _ins(t, "FWHM（半値全幅）\n", "h2")
    _ins(t, "    β = 2 · sqrt(2 · ln 2) · σ  ≈  2.3548 · σ\n\n", "formula")
    _ins(t, "  ピーク最大強度の 1/2 の高さにおける幅。シェラー式の β として使用。\n\n", "bullet")

    _ins(t, "フィット品質: R²（決定係数）\n", "h2")
    _ins(t, "    R² = 1 - SS_res / SS_tot\n\n"
           "    SS_res = Σ (y_i - ŷ_i)²   （残差平方和）\n"
           "    SS_tot = Σ (y_i - ȳ)²     （全平方和）\n\n", "formula")
    _ins(t, "  R² → 1.0 : フィットが良好\n", "bullet")
    _ins(t, "  R² < 0.95 : ピーク範囲の選択や形状を見直す\n\n", "bullet")

    _ins(t, "パラメータの不確かさ（±）\n", "h2")
    _ins(t, "    σ_param = sqrt( diag(pcov) )\n\n", "formula")
    _ins(t, "  scipy.optimize.curve_fit が返す共分散行列 pcov の対角成分の平方根。\n"
           "  結果テーブルの「±」はこの値。R² が高くても ± が大きい場合は再確認を。\n\n", "bullet")

    _ins(t, "注意点\n", "h2")
    _ins(t, "  ・XRD ピークの真の形状は Voigt 関数（Gaussian × Lorentzian の畳み込み）。\n", "bullet")
    _ins(t, "    Gaussian はその近似であり、ピーク裾野でズレが生じることがある。\n", "subbullet")
    _ins(t, "  ・フィットは線形強度値（実測値）で実施。グラフの log 表示とは無関係。\n", "bullet")
    _ins(t, "  ・範囲内に 5 点以上のデータ点が必要。\n", "bullet")
    _ins(t, "  ・フィット収束には初期値推定（ピーク最大値・範囲幅から自動設定）を使用。\n", "bullet")


def _scherrer_content(t):
    _ins(t, "シェラー式（結晶子サイズ）\n", "h1")

    _ins(t, "概要\n", "h2")
    _ins(t, "ピーク幅（FWHM）は結晶子（コヒーレントに回折するドメイン）が小さいほど広くなる。"
           "シェラー式はこの関係を利用して、FWHM から結晶子サイズ D を推定する。"
           "面直測定（θ-2θ スキャン）では D は膜面垂直方向（成長方向）の秩序長さを表す。\n\n", "body")

    _ins(t, "式\n", "h2")
    _ins(t, "    D = K · λ / (β · cos(θ))\n\n", "formula")
    _ins(t, "  D : 結晶子サイズ　[Å]\n", "bullet")
    _ins(t, "  K : シェラー定数 = 0.94（球状結晶を仮定。形状により 0.89〜1.0）\n", "bullet")
    _ins(t, "  λ : X 線波長 = 1.78897 Å　（Co Kα1）\n", "bullet")
    _ins(t, "  β : FWHM [rad]　= FWHM [°] × π / 180\n", "bullet")
    _ins(t, "  θ : ブラッグ角 = (2θ₀) / 2\n\n", "bullet")

    _ins(t, "誤差伝播\n", "h2")
    _ins(t, "    σ_D ≈ D × (σ_β / β)\n\n", "formula")
    _ins(t, "  σ_β は FWHM の標準誤差（Gaussian フィットの共分散行列から取得）。\n"
           "  結果テーブルの D の「±」として表示。\n\n", "bullet")

    _ins(t, "信頼性の判断（アプリ内の表示基準）\n", "h2")
    _ins(t, "  ✓  R² ≥ 0.99 かつ FWHM ≥ 0.1°  → 良好\n", "bullet")
    _ins(t, "  △  FWHM < 0.1°                   → 装置分解能限界付近\n", "bullet")
    _ins(t, "       装置広がり β_inst を差し引いていないため D を過大評価する恐れ。\n", "subbullet")
    _ins(t, "       補正式: β_size = sqrt(β_obs² - β_inst²)\n", "subbullet")
    _ins(t, "  ✗  R² < 0.95                      → フィット自体が不良\n\n", "bullet")

    _ins(t, "D の値の目安（面直測定）\n", "h2")
    _ins(t, "  D < 100 Å    : ナノ結晶・高密度欠陥や粒界が多い\n", "bullet")
    _ins(t, "  D 100〜1000 Å: 通常の薄膜域\n", "bullet")
    _ins(t, "  D > 1000 Å   : 装置分解能限界に近い（参考値として扱う）\n\n", "bullet")

    _ins(t, "本質的な限界\n", "h2")
    _ins(t, "  ・装置分解能補正（標準試料で β_inst を実測）を行っていない。\n", "bullet")
    _ins(t, "  ・格子歪み（microstrain）によるブロードニングと区別できない。\n", "bullet")
    _ins(t, "     分離するには Williamson-Hall 法が必要（本アプリ未実装）。\n", "subbullet")
    _ins(t, "  ・精度の目安: 理想条件でも ±10〜30%。\n", "bullet")
