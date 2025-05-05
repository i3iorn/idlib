from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

from PyQt6.QtWidgets import QVBoxLayout, QComboBox, QHBoxLayout, QLabel, QPushButton, QWidget

from api_viewer.constants import NO_MARGIN
from api_viewer.log.decorator import log_method_calls


class ControlKey(Enum):
    API = "api"
    ENDPOINT = "endpoint"
    CLIENT = "client"


@dataclass
class ConfigState:
    api_spec: Any = None
    endpoint_path: str = ""
    client_spec: Any = None
    prodtest: bool = False


@log_method_calls()
class UIFactory:
    @staticmethod
    def combo(label: str, parent_layout: QVBoxLayout) -> QComboBox:
        combo = QComboBox()
        combo.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
        combo.setDuplicatesEnabled(False)
        combo.setMaxVisibleItems(10)
        combo.setMinimumContentsLength(20)
        row = QHBoxLayout()
        row.setContentsMargins(*NO_MARGIN)
        row.addWidget(QLabel(f"{label}:"), 1)
        row.addWidget(combo, 3)
        parent_layout.addLayout(row)
        return combo

    @staticmethod
    def button(label: str, height: int = 30) -> QPushButton:
        btn = QPushButton(label)
        btn.setFixedHeight(height)
        return btn


@log_method_calls()
class DynamicControlManager:
    def __init__(self, layout: QVBoxLayout):
        self._layout = layout
        self._controls: Dict[str, QWidget] = {}

    def add(self, key: str, widget: QWidget) -> None:
        self.clear(key)
        self._controls[key] = widget
        self._layout.addWidget(widget)

    def clear(self, key: str) -> None:
        if widget := self._controls.pop(key, None):
            self._layout.removeWidget(widget)
            widget.deleteLater()

    def clear_all(self) -> None:
        for key in list(self._controls):
            self.clear(key)

    @property
    def controls(self) -> Dict[str, QWidget]:
        return self._controls

    def keys(self):
        return self._controls.keys()
