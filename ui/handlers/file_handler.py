import os
import logging
import tkinter as tk
from tkinter import filedialog, messagebox
from core import data_analyzer

logger = logging.getLogger(__name__)


class FileHandler:
    """ファイル操作やリストボックスの管理を行うハンドラクラスである。"""

    def __init__(self, app, model):
        self.app = app
        self.model = model

    def _add_file_if_valid(self, filepath, select_after=False):
        """
        ファイルが有効であれば読み込み、データを保持する。
        追加に成功した場合はTrueを返す。
        """
        if filepath in self.app.file_data:
            return False

        angles, intensities = data_analyzer.parse_ras_file(filepath)
        if angles is None or intensities is None:
            logger.warning(f"File reading failed: {filepath}")
            messagebox.showwarning(
                "警告",
                f"ファイル {os.path.basename(filepath)} の読み込みに失敗した。",
                parent=self.app.master,
            )
            return False

        self.app.parsed_data[filepath] = (angles, intensities)
        self.app.file_data[filepath] = os.path.basename(filepath)
        self.app.file_listbox.insert(tk.END, filepath)

        if select_after:
            self.app.file_listbox.selection_clear(0, tk.END)
            self.app.file_listbox.selection_set(tk.END)
            self.on_file_select(None)

        self.add_to_recent(filepath)
        return True

    def add_to_recent(self, filepath):
        """最近使ったファイルリストに追加する。"""
        if filepath in self.app.recent_files:
            self.app.recent_files.remove(filepath)
        self.app.recent_files.insert(0, filepath)
        if len(self.app.recent_files) > 10:
            self.app.recent_files = self.app.recent_files[:10]
        self.update_recent_menu()

    def update_recent_menu(self):
        """最近使ったファイルのメニューを更新する。"""
        self.app.recent_menu.delete(0, tk.END)
        if not self.app.recent_files:
            self.app.recent_menu.add_command(label="(履歴なし)", state="disabled")
        else:
            for fp in self.app.recent_files:
                display_name = fp if len(fp) < 60 else "..." + fp[-57:]
                self.app.recent_menu.add_command(
                    label=display_name, command=lambda f=fp: self.open_recent_file(f)
                )
            self.app.recent_menu.add_separator()
            self.app.recent_menu.add_command(
                label="履歴をクリア", command=self.clear_recent_files
            )

    def clear_recent_files(self):
        """最近使ったファイルの履歴をクリアする。"""
        self.app.recent_files = []
        self.update_recent_menu()

    def open_recent_file(self, filepath):
        """最近使ったファイルを開く。"""
        if not os.path.exists(filepath):
            messagebox.showerror(
                "エラー", f"ファイルが見つからない:\n{filepath}", parent=self.app.master
            )
            if filepath in self.app.recent_files:
                self.app.recent_files.remove(filepath)
                self.update_recent_menu()
            return

        if self._add_file_if_valid(filepath, select_after=True):
            self.app.schedule_update()

    def on_drop_files(self, event):
        """ファイルをドラッグ＆ドロップした際の処理を行う。"""
        files = self.app.master.tk.splitlist(event.data)
        added_any = False
        for fp in files:
            if self._add_file_if_valid(fp):
                added_any = True

        if added_any and not self.app.file_listbox.curselection():
            self.app.file_listbox.selection_set(tk.END)
            self.on_file_select(None)

        if added_any:
            self.app.schedule_update()

    def select_files(self):
        """ファイル選択ダイアログを開き、ファイルを追加する。"""
        filepaths = filedialog.askopenfilenames(
            title="XRDファイルを選択",
            filetypes=[("RAS files", "*.ras"), ("All files", "*.*")],
        )
        if not filepaths:
            return

        added_any = False
        for fp in filepaths:
            if self._add_file_if_valid(fp):
                added_any = True

        if added_any and not self.app.file_listbox.curselection():
            self.app.file_listbox.selection_set(tk.END)
            self.on_file_select(None)

        if added_any:
            self.app.schedule_update()

    def remove_selected_file(self):
        """選択されているファイルをリストから削除する。"""
        selected_indices = self.app.file_listbox.curselection()
        if not selected_indices:
            return

        selected_filepath = self.app.file_listbox.get(selected_indices[0])
        if selected_filepath in self.app.file_data:
            del self.app.file_data[selected_filepath]
        if selected_filepath in self.app.parsed_data:
            del self.app.parsed_data[selected_filepath]

        self.app.file_listbox.delete(selected_indices[0])
        self.app.legend_name_entry.config(state="disabled")
        self.model.legend_name_var.set("")

        if self.app.file_listbox.size() > 0:
            new_selection_index = min(
                selected_indices[0], self.app.file_listbox.size() - 1
            )
            self.app.file_listbox.selection_set(new_selection_index)
            self.on_file_select(None)

        self.app.schedule_update()

    def move_file_up(self):
        """選択されたファイルをリストの上へ移動する。"""
        selected_indices = self.app.file_listbox.curselection()
        if not selected_indices:
            return
        idx = selected_indices[0]
        if idx > 0:
            filepath = self.app.file_listbox.get(idx)
            self.app.file_listbox.delete(idx)
            self.app.file_listbox.insert(idx - 1, filepath)
            self.app.file_listbox.selection_set(idx - 1)
            self.app.schedule_update()

    def move_file_down(self):
        """選択されたファイルをリストの下へ移動する。"""
        selected_indices = self.app.file_listbox.curselection()
        if not selected_indices:
            return
        idx = selected_indices[0]
        if idx < self.app.file_listbox.size() - 1:
            filepath = self.app.file_listbox.get(idx)
            self.app.file_listbox.delete(idx)
            self.app.file_listbox.insert(idx + 1, filepath)
            self.app.file_listbox.selection_set(idx + 1)
            self.app.schedule_update()

    def on_file_select(self, event):
        """リストボックスでファイルが選択された時の処理を行う。"""
        selected_indices = self.app.file_listbox.curselection()
        if not selected_indices:
            self.app.legend_name_entry.config(state="disabled")
            self.model.legend_name_var.set("")
            return
        selected_filepath = self.app.file_listbox.get(selected_indices[0])
        self.model.legend_name_var.set(self.app.file_data.get(selected_filepath, ""))
        self.app.legend_name_entry.config(state="normal")

    def on_legend_name_change(self, *args):
        """凡例名が変更された時の処理を行う。"""
        selected_indices = self.app.file_listbox.curselection()
        if selected_indices:
            selected_filepath = self.app.file_listbox.get(selected_indices[0])
            self.app.file_data[selected_filepath] = self.model.legend_name_var.get()
            self.app.schedule_update()
