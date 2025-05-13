from typing import Dict

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from api_viewer.emitter import signal_emitter
from api_viewer.log.decorator import log_method_calls


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
