import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from core.config_manager import ConfigManager
from core import data_analyzer


class SettingsHandler:
    """設定の保存や読み込みを管理するハンドラクラスである。"""

    def __init__(self, app, model):
        self.app = app
        self.model = model

    # ------------------------------------------------------------------ #
    # 起動設定（preferences.json）
    # ------------------------------------------------------------------ #

    def _prefs_path(self) -> str:
        return os.path.join(os.path.dirname(self.app.config_file), "preferences.json")

    def _load_prefs(self) -> dict:
        try:
            with open(self._prefs_path(), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_prefs(self, prefs: dict):
        try:
            with open(self._prefs_path(), "w", encoding="utf-8") as f:
                json.dump(prefs, f, indent=2)
        except Exception:
            pass

    def get_restore_on_startup(self) -> bool:
        return self._load_prefs().get("restore_on_startup", True)

    def set_restore_on_startup(self, value: bool):
        prefs = self._load_prefs()
        prefs["restore_on_startup"] = value
        self._save_prefs(prefs)

    def build_config_dict(self, include_recent=False) -> dict:
        """現在のUIの入力状態から設定辞書を構築する。"""
        settings = {
            "files": {
                "filepaths": list(self.app.file_listbox.get(0, tk.END)),
                "file_data": self.app.file_data,
            },
            "variables": {
                var_name: getattr(self.model, var_name).get()
                for var_name in self.model.savable_vars
            },
            "reference_peaks": [
                {
                    "name": self.model.peak_name_vars[i].get(),
                    "angle": self.model.peak_angle_vars[i].get(),
                    "visible": self.model.peak_visible_vars[i].get(),
                    "color": self.model.peak_color_vars[i].get(),
                    "style": self.model.peak_style_vars[i].get(),
                }
                for i in range(len(self.model.peak_name_vars))
            ],
        }
        if include_recent:
            settings["recent_files"] = self.app.recent_files
        return settings

    def apply_config_dict(self, settings: dict, is_app_config: bool = False):
        """設定辞書を読み込み、UIに反映させる。"""
        if is_app_config and "recent_files" in settings:
            self.app.recent_files = settings["recent_files"]
            self.app.file_handler.update_recent_menu()

        if not is_app_config:
            self.app.file_listbox.delete(0, tk.END)
            self.app.file_data.clear()
            self.app.parsed_data.clear()
            self.app.legend_name_entry.config(state="disabled")
            self.model.legend_name_var.set("")

        loaded_filepaths = settings.get("files", {}).get("filepaths", [])
        loaded_file_data = settings.get("files", {}).get("file_data", {})

        for fp in loaded_filepaths:
            if os.path.exists(fp):
                angles, intensities = data_analyzer.parse_ras_file(fp)
                if angles is not None and intensities is not None:
                    self.app.parsed_data[fp] = (angles, intensities)
                    self.app.file_data[fp] = loaded_file_data.get(
                        fp, os.path.basename(fp)
                    )
                    self.app.file_listbox.insert(tk.END, fp)
                elif not is_app_config:
                    messagebox.showwarning(
                        "警告",
                        f"ファイル {os.path.basename(fp)} の読み込みに失敗した。スキップする。",
                        parent=self.app.master,
                    )
            elif not is_app_config:
                messagebox.showwarning(
                    "警告",
                    f"ファイルが見つからない: {fp}\nこのファイルはスキップされた。",
                    parent=self.app.master,
                )

        if self.app.file_listbox.size() > 0:
            self.app.file_listbox.selection_set(0)
            self.app.file_handler.on_file_select(None)

        if "variables" in settings:
            for var_name, value in settings["variables"].items():
                if hasattr(self.model, var_name):
                    try:
                        getattr(self.model, var_name).set(value)
                    except Exception:
                        pass
        elif "export_format" in settings:  # 下位互換性のため
            self.model.export_format_var.set(settings["export_format"])
            if "export_width" in settings:
                self.model.export_width_var.set(settings["export_width"])
            if "export_height" in settings:
                self.model.export_height_var.set(settings["export_height"])

        if "reference_peaks" in settings:
            for i, peak_data in enumerate(settings["reference_peaks"]):
                if i < len(self.model.peak_name_vars):
                    self.model.peak_name_vars[i].set(peak_data.get("name", ""))
                    self.model.peak_angle_vars[i].set(peak_data.get("angle", ""))
                    self.model.peak_visible_vars[i].set(peak_data.get("visible", False))
                    color = peak_data.get("color", "#000000")
                    self.model.peak_color_vars[i].set(color)
                    self.app.peak_color_buttons[i].config(fg=color)
                    style_val = peak_data.get("style", "--")
                    self.model.peak_style_vars[i].set(style_val)
                    _ls_rev = {"-": "実線", "--": "破線", ":": "点線", "-.": "一点鎖線"}
                    if hasattr(self.app, "peak_style_combos") and i < len(self.app.peak_style_combos):
                        self.app.peak_style_combos[i].set(_ls_rev.get(style_val, "破線"))

        self.app._toggle_spacing_widget()
        self.app._toggle_minor_xticks_widgets()
        self.app.schedule_update()

    def save_settings(self):
        """現在のプロット設定をJSONファイルとして保存する。"""
        default_filename = ""
        if self.app.file_listbox.size() > 0:
            first_filepath = self.app.file_listbox.get(0)
            legend_name = self.app.file_data.get(first_filepath, "")
            default_filename = os.path.splitext(legend_name)[0]

        filepath = filedialog.asksaveasfilename(
            title="設定を保存",
            initialfile=default_filename,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            defaultextension=".json",
            parent=self.app.master,
        )
        if not filepath:
            return

        settings = self.build_config_dict()
        if ConfigManager.save_to_file(filepath, settings):
            messagebox.showinfo(
                "成功", f"設定を保存した:\n{filepath}", parent=self.app.master
            )
        else:
            messagebox.showerror(
                "エラー", "設定の保存中にエラーが発生した", parent=self.app.master
            )

    def load_settings(self):
        """JSONファイルからプロット設定を読み込む。"""
        filepath = filedialog.askopenfilename(
            title="設定を読み込む",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            parent=self.app.master,
        )
        if not filepath:
            return

        settings = ConfigManager.load_from_file(filepath)
        if settings is None:
            messagebox.showerror(
                "エラー", "設定の読み込みに失敗した", parent=self.app.master
            )
            return

        self.apply_config_dict(settings, is_app_config=False)
        messagebox.showinfo("成功", "設定を読み込んだ。", parent=self.app.master)

    def load_app_config(self):
        """起動時のアプリケーション設定を読み込む。preferences で無効化されていればスキップ。"""
        if not self.get_restore_on_startup():
            return
        settings = ConfigManager.load_from_file(self.app.config_file)
        if not settings:
            return
        answer = messagebox.askyesno(
            "セッションの復元",
            "前回のセッション（ファイル・設定）を復元しますか？",
            parent=self.app.master,
        )
        if answer:
            self.apply_config_dict(settings, is_app_config=True)

    def save_app_config(self):
        """終了時のアプリケーション設定を保存する。"""
        settings = self.build_config_dict(include_recent=True)
        ConfigManager.save_to_file(self.app.config_file, settings)
