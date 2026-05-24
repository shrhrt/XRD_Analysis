import os
import sys
import logging
from tkinterdnd2 import TkinterDnD
import sv_ttk
from ui.main_window import MainWindow
from ui import style_manager


def _asset_path(relative_path):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


def setup_logging():
    log_dir = os.path.join(os.path.expanduser("~"), ".xrd_plotter")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "xrd_plotter.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger(__name__)


def main():
    logger = setup_logging()
    logger.info("XRD Plotter アプリケーションを起動しました。")

    root = TkinterDnD.Tk()
    sv_ttk.set_theme("light")
    style_manager.apply("light")

    icon_path = _asset_path(os.path.join("assets", "XRD_ANALYSIS_ICON.ico"))
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)

    root.state("zoomed")
    app = MainWindow(master=root)
    app.mainloop()


if __name__ == "__main__":
    main()
