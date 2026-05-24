import tkinter as tk
from tkinter import ttk


def show_theory_dialog(master):
    """理論・計算式の解説ウィンドウを開く"""
    win = tk.Toplevel(master)
    win.title("理論・計算式の解説")
    win.geometry("700x560")
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


def _build_text(parent, builder):
    parent.rowconfigure(0, weight=1)
    parent.columnconfigure(0, weight=1)

    text = tk.Text(
        parent, wrap=tk.WORD, padx=18, pady=12,
        relief="flat", bd=0,
    )
    vsb = ttk.Scrollbar(parent, orient="vertical", command=text.yview)
    text.configure(yscrollcommand=vsb.set)
    text.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")

    text.tag_configure("h1",
        font=("", 14, "bold"), spacing1=10, spacing3=6)
    text.tag_configure("h2",
        font=("", 11, "bold"), spacing1=8, spacing3=3, foreground="#1a5276")
    text.tag_configure("formula",
        font=("Courier New", 10),
        lmargin1=24, lmargin2=24, spacing1=6, spacing3=6)
    text.tag_configure("body",
        font=("", 10), spacing1=3)
    text.tag_configure("bullet",
        font=("", 10), lmargin1=22, lmargin2=34, spacing1=2)
    text.tag_configure("subbullet",
        font=("", 10), lmargin1=38, lmargin2=50,
        spacing1=1, foreground="#555555")

    builder(text)
    text.config(state="disabled")


def _i(t, s, tag="body"):
    t.insert(tk.END, s, tag)


# ------------------------------------------------------------------ #

def _bragg_content(t):
    _i(t, "ブラッグの法則\n", "h1")

    _i(t, "概要\n", "h2")
    _i(t, "X 線が結晶の格子面（間隔 d の等間隔面群）で反射するとき、"
          "隣接面からの反射波の光路差が波長の整数倍になれば強め合う。"
          "この条件がブラッグの法則であり、ピーク位置 2θ を測定することで"
          "面間隔 d を直接求めることができる。\n\n")

    _i(t, "式\n", "h2")
    _i(t, "    n*lambda = 2d * sin(theta)\n\n", "formula")

    _i(t, "各記号\n", "h2")
    _i(t, "  n      : 回折次数（通常 n = 1）\n", "bullet")
    _i(t, "  lambda : X 線波長  Co Kalpha1 = 1.78897 Angstrom\n", "bullet")
    _i(t, "  d      : 結晶面間隔 d-spacing  [Angstrom]\n", "bullet")
    _i(t, "  theta  : ブラッグ角（測定角 2theta の半分）\n\n", "bullet")

    _i(t, "d の算出式（本アプリの計算）\n", "h2")
    _i(t, "    d = lambda / (2 * sin(theta))\n"
          "    where theta = (測定 2theta) / 2\n\n", "formula")

    _i(t, "高次反射について\n", "h2")
    _i(t, "  MgO の 001 面を n=2 で測定したものは「002 反射」と表記し、\n", "bullet")
    _i(t, "  d_002 = d_001 / 2 となる。\n", "bullet")
    _i(t, "  本アプリは n=1 固定。002, 004, 008 はそれぞれ独立した d として計算する。\n\n", "bullet")


def _lattice_content(t):
    _i(t, "格子定数計算（立方晶）\n", "h1")

    _i(t, "概要\n", "h2")
    _i(t, "立方晶系では全軸が等長（a = b = c）で直交するため、"
          "面間隔 d と格子定数 a の関係が簡単な式で表せる。"
          "ブラッグの法則で求めた d に面指数 hkl を与えると a が計算できる。\n\n")

    _i(t, "立方晶の面間隔\n", "h2")
    _i(t, "    d_hkl = a / sqrt(h^2 + k^2 + l^2)\n\n", "formula")

    _i(t, "格子定数の計算式（本アプリの計算）\n", "h2")
    _i(t, "    a = d_hkl * sqrt(h^2 + k^2 + l^2)\n\n", "formula")

    _i(t, "各記号\n", "h2")
    _i(t, "  a      : 格子定数 [Angstrom]\n", "bullet")
    _i(t, "  d_hkl  : (hkl) 面の面間隔（ブラッグの法則から取得）[Angstrom]\n", "bullet")
    _i(t, "  h, k, l: ミラー指数\n\n", "bullet")

    _i(t, "計算例\n", "h2")
    _i(t, "  MgO 002  (d = 2.106 A)  →  a = 2.106 * sqrt(0+0+4) = 2.106 * 2 = 4.212 A\n", "bullet")
    _i(t, "  Fe3O4 004 (d = 2.099 A) →  a = 2.099 * sqrt(0+0+16) = 2.099 * 4 = 8.396 A\n", "bullet")
    _i(t, "  Fe3O4 008 (d = 1.050 A) →  a = 1.050 * sqrt(0+0+64) = 1.050 * 8 = 8.400 A\n\n", "bullet")
    _i(t, "  004 と 008 は同じ物質なので a がほぼ一致する。\n"
          "  複数の反射で a を比較することで測定精度を確認できる。\n\n", "subbullet")

    _i(t, "注意点\n", "h2")
    _i(t, "  本アプリは立方晶のみ対応。正方晶・六方晶等は異なる式が必要。\n", "bullet")
    _i(t, "  正方晶 : 1/d^2 = (h^2+k^2)/a^2 + l^2/c^2\n", "subbullet")
    _i(t, "  六方晶 : 1/d^2 = 4(h^2+hk+k^2)/(3a^2) + l^2/c^2\n\n", "subbullet")


def _gaussian_content(t):
    _i(t, "Gaussian フィッティング\n", "h1")

    _i(t, "概要\n", "h2")
    _i(t, "XRD ピークを Gaussian 関数でフィットすることで、測定データ点の間隔に縛られない"
          "精密なピーク位置・FWHM を抽出する。"
          "これによりシェラー式への入力となる FWHM が得られる。\n\n")

    _i(t, "フィットモデル\n", "h2")
    _i(t, "    I(2theta) = A * exp( -(2theta - 2theta0)^2 / (2*sigma^2) )\n"
          "              + a * 2theta + b\n\n", "formula")
    _i(t, "  A        : ピーク振幅（バックグラウンドを差し引いた最大強度）\n", "bullet")
    _i(t, "  2theta0  : ピーク中心位置 [deg]  ← d 値・格子定数の計算に使用\n", "bullet")
    _i(t, "  sigma    : 標準偏差 [deg]\n", "bullet")
    _i(t, "  a, b     : 線形バックグラウンドの傾きと切片\n\n", "bullet")
    _i(t, "  線形バックグラウンドを同時フィットするため、背景を手動除去しなくてよい。\n\n",
          "subbullet")

    _i(t, "FWHM（半値全幅）\n", "h2")
    _i(t, "    beta = 2 * sqrt(2 * ln2) * sigma  =  2.3548 * sigma\n\n", "formula")
    _i(t, "  ピーク最大強度の 1/2 の高さにおける幅。シェラー式の beta として使用。\n\n",
          "bullet")

    _i(t, "フィット品質: R^2（決定係数）\n", "h2")
    _i(t, "    R^2 = 1 - SS_res / SS_tot\n\n"
          "    SS_res = sum( (y_i - y_fit_i)^2 )   残差平方和\n"
          "    SS_tot = sum( (y_i - y_mean)^2 )     全平方和\n\n", "formula")
    _i(t, "  R^2 → 1.0 : フィットが良好\n", "bullet")
    _i(t, "  R^2 < 0.95: ピーク範囲の選択や形状を見直す\n\n", "bullet")

    _i(t, "パラメータの不確かさ（±）\n", "h2")
    _i(t, "    sigma_param = sqrt( diag(pcov) )\n\n", "formula")
    _i(t, "  scipy.optimize.curve_fit が返す共分散行列 pcov の対角成分の平方根。\n"
          "  結果テーブルの「±」はこの値。\n\n", "bullet")

    _i(t, "注意点\n", "h2")
    _i(t, "  XRD ピークの真の形状は Voigt 関数（Gaussian と Lorentzian の畳み込み）。\n", "bullet")
    _i(t, "  Gaussian はその近似であり、ピーク裾野でズレが生じることがある。\n", "subbullet")
    _i(t, "  フィットは線形強度値（実測値）で実施。グラフの log 表示とは無関係。\n", "bullet")
    _i(t, "  範囲内に 5 点以上のデータ点が必要。\n", "bullet")


def _scherrer_content(t):
    _i(t, "シェラー式（結晶子サイズ）\n", "h1")

    _i(t, "概要\n", "h2")
    _i(t, "ピーク幅（FWHM）は結晶子（コヒーレントに回折するドメイン）が小さいほど広くなる。"
          "シェラー式はこの関係を利用して FWHM から結晶子サイズ D を推定する。"
          "面直測定（theta-2theta スキャン）では D は膜面垂直方向（成長方向）の秩序長さを表す。\n\n")

    _i(t, "式\n", "h2")
    _i(t, "    D = K * lambda / (beta * cos(theta))\n\n", "formula")
    _i(t, "  D      : 結晶子サイズ [Angstrom]\n", "bullet")
    _i(t, "  K      : シェラー定数 = 0.94  （球状結晶を仮定。形状により 0.89〜1.0）\n", "bullet")
    _i(t, "  lambda : X 線波長 = 1.78897 Angstrom  （Co Kalpha1）\n", "bullet")
    _i(t, "  beta   : FWHM [rad]  = FWHM [deg] * pi / 180\n", "bullet")
    _i(t, "  theta  : ブラッグ角 = 2theta0 / 2\n\n", "bullet")

    _i(t, "誤差伝播\n", "h2")
    _i(t, "    sigma_D = D * (sigma_beta / beta)\n\n", "formula")
    _i(t, "  sigma_beta は FWHM の標準誤差（Gaussian フィットの共分散行列から取得）。\n"
          "  結果テーブルの D の「±」として表示。\n\n", "bullet")

    _i(t, "信頼性の判断（アプリ内の表示基準）\n", "h2")
    _i(t, "  [ok] R^2 >= 0.99 かつ FWHM >= 0.1 deg  : 良好\n", "bullet")
    _i(t, "  [caution] FWHM < 0.1 deg               : 装置分解能限界付近\n", "bullet")
    _i(t, "    装置広がり beta_inst を差し引いていないため D を過大評価する恐れ。\n", "subbullet")
    _i(t, "    補正式: beta_size = sqrt(beta_obs^2 - beta_inst^2)\n", "subbullet")
    _i(t, "  [poor] R^2 < 0.95                       : フィット自体が不良\n\n", "bullet")

    _i(t, "D の値の目安（面直測定）\n", "h2")
    _i(t, "  D < 100 A    : ナノ結晶・高密度欠陥や粒界が多い\n", "bullet")
    _i(t, "  D 100〜1000 A: 通常の薄膜域\n", "bullet")
    _i(t, "  D > 1000 A   : 装置分解能限界に近い（参考値として扱う）\n\n", "bullet")

    _i(t, "本質的な限界\n", "h2")
    _i(t, "  装置分解能補正（標準試料で beta_inst を実測）を行っていない。\n", "bullet")
    _i(t, "  格子歪み（microstrain）によるブロードニングと区別できない。\n", "bullet")
    _i(t, "  分離するには Williamson-Hall 法が必要（本アプリ未実装）。\n", "subbullet")
    _i(t, "  精度の目安: 理想条件でも ±10〜30%。\n", "bullet")
