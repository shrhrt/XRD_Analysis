import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    設定データのJSONファイルへの保存および読み込みを担当するクラス
    """

    @staticmethod
    def save_to_file(filepath: str, config_data: Dict[str, Any]) -> bool:
        """
        設定辞書をJSONファイルとして保存します。
        """
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"設定の保存中にエラーが発生しました: {e}", exc_info=True)
            return False

    @staticmethod
    def load_from_file(filepath: str) -> Optional[Dict[str, Any]]:
        """
        JSONファイルから設定辞書を読み込みます。
        """
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"設定ファイルの形式が不正です: {e}")
            return None
        except Exception as e:
            logger.error(f"設定の読み込み中にエラーが発生しました: {e}", exc_info=True)
            return None
