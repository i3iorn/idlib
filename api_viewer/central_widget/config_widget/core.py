from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Union, Iterable

from PyQt6.QtWidgets import QVBoxLayout, QComboBox, QHBoxLayout, QLabel, QPushButton, QWidget, QCheckBox, QBoxLayout

from api_viewer.constants import NO_MARGIN
from api_viewer.emitter import signal_emitter
from api_viewer.log.decorator import log_method_calls


class ControlKey(Enum):
    API = "api"
    ENDPOINT = "endpoint"
    CLIENT = "client"
    PRODTEST = "prodtest"
    EXTERNAL = "external"

class ControlType(Enum):
    COMBO = QComboBox
    BUTTON = QPushButton
    CHECKBOX = QCheckBox


class ControlKeyType(Enum):
    API = ControlType.COMBO
    ENDPOINT = ControlType.COMBO
    CLIENT = ControlType.COMBO
    PRODTEST = ControlType.CHECKBOX
    EXTERNAL = ControlType.CHECKBOX


@dataclass
class ConfigState:
    api_spec: Any = None
    endpoint_path: str = ""
    client_spec: Any = None
    prodtest: bool = False
    external: bool = False

    def set_api_spec(self, api_spec: Any) -> None:
        self.api_spec = api_spec

    def set_endpoint(self, endpoint_path: str) -> None:
        self.endpoint_path = endpoint_path


@log_method_calls()
class UIFactory:
    @staticmethod
    def populate_combo(combo: QComboBox, items: Union[Dict, Iterable]):
        combo.clear()
        if isinstance(items, dict):
            for name, data in items.items():
                combo.addItem(name, data)
        else:
            for item in items:
                name = getattr(item, "name", str(item))
                combo.addItem(name, item)
        combo.setCurrentIndex(0)

    @classmethod
    def widget(cls, control_type: ControlType, label: str, parent_layout: QBoxLayout) -> QWidget:
        if control_type == ControlType.COMBO:
            return cls.combo(label, parent_layout)
        elif control_type == ControlType.BUTTON:
            return cls.button(label, parent_layout)
        elif control_type == ControlType.CHECKBOX:
            return cls.checkbox(label, parent_layout)
        else:
            raise ValueError(f"Unsupported control type: {control_type}")

    @staticmethod
    def combo(label: str, parent_layout: QBoxLayout) -> QComboBox:
        combo = QComboBox()
        combo.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
        combo.setDuplicatesEnabled(False)
        combo.setMaxVisibleItems(10)
        combo.setMinimumContentsLength(20)
        row = QHBoxLayout()
        row.setContentsMargins(*NO_MARGIN)
        row.addWidget(QLabel(f"{label}:"), 2)
        row.addWidget(combo, 3)
        parent_layout.addLayout(row)
        return combo

    @staticmethod
    def button(label: str, parent_layout: QBoxLayout, height: int = 30) -> QPushButton:
        btn = QPushButton(label)
        btn.setFixedHeight(height)
        if parent_layout is not None:
            parent_layout.addWidget(btn)
        return btn

    @staticmethod
    def checkbox(label: str, parent_layout: QBoxLayout) -> QWidget:
        checkbox = QCheckBox()
        checkbox.setContentsMargins(*NO_MARGIN)
        lbl = QLabel(label)
        lbl.setContentsMargins(*NO_MARGIN)
        row = QHBoxLayout()
        row.setContentsMargins(*NO_MARGIN)
        row.addWidget(lbl, 2)
        row.addWidget(checkbox, 3)
        parent_layout.addLayout(row)
        return checkbox


@log_method_calls()
class DynamicControlManager:
    def __init__(self, layout: QVBoxLayout):
        self._layout = layout
        self._controls: Dict[str, QWidget] = {}

    def add(self, key: str, widget: QWidget) -> None:
        self.clear(key)
        self._controls[key] = widget
        self._layout.addWidget(widget)
        signal_emitter.dynamicControlUpdated.emit()

    def clear(self, key: str) -> None:
        if widget := self._controls.pop(key, None):
            self._layout.removeWidget(widget)
            widget.deleteLater()
        signal_emitter.dynamicControlUpdated.emit()

    def clear_all(self) -> None:
        for key in list(self._controls):
            self.clear(key)
        signal_emitter.dynamicControlUpdated.emit()

    def set_all_enabled(self, enabled: bool) -> None:
        for widget in self._controls.values():
            widget.setEnabled(enabled)
        signal_emitter.dynamicControlUpdated.emit()

    @property
    def controls(self) -> Dict[str, QWidget]:
        return self._controls

    def keys(self):
        return self._controls.keys()
