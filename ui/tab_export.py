from tkinter import ttk
from ui import style_manager


class ExportTab:
    """エクスポートタブのUIを構築するクラス"""

    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.build()

    def build(self):
        export_frame = ttk.LabelFrame(self.parent, text="画像ファイルとして保存")
        export_frame.pack(fill="x", padx=10, pady=10)
        export_frame.columnconfigure(1, weight=1)

        ttk.Label(export_frame, text="幅 (inch):").grid(
            row=0, column=0, sticky="w", padx=5, pady=2
        )
        ttk.Entry(export_frame, textvariable=self.app.model.export_width_var).grid(
            row=0, column=1, sticky="ew", padx=5, pady=2
        )

        ttk.Label(export_frame, text="高さ (inch):").grid(
            row=1, column=0, sticky="w", padx=5, pady=2
        )
        ttk.Entry(export_frame, textvariable=self.app.model.export_height_var).grid(
            row=1, column=1, sticky="ew", padx=5, pady=2
        )

        ttk.Label(export_frame, text="形式:").grid(
            row=2, column=0, sticky="w", padx=5, pady=2
        )
        ttk.Combobox(
            export_frame,
            textvariable=self.app.model.export_format_var,
            values=["png", "pdf", "svg"],
            state="readonly",
        ).grid(row=2, column=1, sticky="ew", padx=5, pady=2)

        button_frame = ttk.Frame(export_frame)
        button_frame.grid(
            row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=(10, 5)
        )
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        ttk.Button(
            button_frame,
            text="プレビュー",
            command=self.app.plot_handler.preview_figure,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 2))
        style_manager.primary_btn(
            button_frame,
            text="グラフを保存",
            command=self.app.plot_handler.save_figure,
        ).grid(row=0, column=1, sticky="ew", padx=(2, 0))
