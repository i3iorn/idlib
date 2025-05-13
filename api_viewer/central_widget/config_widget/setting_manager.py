from typing import Any

from PyQt6.QtCore import QSettings

from api_viewer.central_widget.config_widget.utils import ControlKey
from api_viewer.log.decorator import log_method_calls


@log_method_calls()
class SettingsManager:
    def __init__(self, settings: QSettings):
        self._settings = settings

    def load_index(self, key: ControlKey, default: int = 0) -> int:
        return self._settings.value(f"{key.name}Index", default, int)

    def save_index(self, key: ControlKey, index: int) -> None:
        self._settings.setValue(f"{key.name}Index", index)

    def load_text(self, key: str) -> str:
        return self._settings.value(key, "")

    def save_text(self, key: str, text: str) -> None:
        self._settings.setValue(key, text)

    def save_flag(self, key: Any, flag: bool) -> None:
        self._settings.setValue(key.name, flag)

    def load_flag(self, key: Any, default: bool = False) -> bool:
        return self._settings.value(key.name, default, bool)
