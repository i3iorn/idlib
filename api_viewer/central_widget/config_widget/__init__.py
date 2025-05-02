import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, Iterable, Any, Optional

from qasync import asyncSlot
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtWidgets import QVBoxLayout, QComboBox, QLabel, QHBoxLayout, QPushButton, \
    QMessageBox, QSplitter, QWidget, QCheckBox, QSizePolicy, QSpacerItem, QProgressBar

from api_viewer.api.request_handler import APIRequestHandler
from api_viewer.central_widget.core import CentralChildWidget
from api_viewer.constants import NO_MARGIN
from api_viewer.json_text_edit import JsonTextEdit
from api_viewer.log.decorator import log_method_calls

logger = logging.getLogger(__name__)


class WidgetCreator:
    @classmethod
    def create_widget(cls, widget_class, parent=None):
        """
        Create a widget of the specified class.
        """
        widget = widget_class(parent)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        return widget

    @classmethod
    def created_labeled_widget(cls, widget_class, label_text: str, layout: QVBoxLayout):
        """
        Create a labeled widget of the specified class.
        """
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(*NO_MARGIN)

        label = QLabel(label_text)
        widget = cls.create_widget(widget_class)

        h_layout.addWidget(label, 1)
        h_layout.addWidget(widget, 3)
        layout.addLayout(h_layout)

        return widget

    @classmethod
    def create_labeled_combobox(cls, label_text: str, layout: QVBoxLayout) -> QComboBox:
        """
        Create a labeled combo box.
        """
        return cls.created_labeled_widget(QComboBox, label_text, layout)

    @classmethod
    def create_labeled_checkbox(cls, label_text: str, layout: QVBoxLayout) -> QCheckBox:
        """
        Create a labeled checkbox.
        """
        return cls.created_labeled_widget(QCheckBox, label_text, layout)



dynamic_layout_key = Qt.ItemDataRole.UserRole + 1

@dataclass
class ConfigState:
    api_spec: Any = None
    endpoint_path: str = ""
    client_spec: Any = None
    specific: Dict[str, Any] = field(default_factory=dict)
    prodtest: bool = False
    body: Dict[str, Any] = field(default_factory=dict)


class DynamicControlManager:
    def __init__(self, layout: QVBoxLayout):
        self.layout = layout
        self.controls: Dict[str, QWidget] = {}

    def add(self, key: str, widget: QWidget):
        self.clear(key)
        self.controls[key] = widget
        self.layout.addWidget(widget)

    def clear(self, key: str):
        if key in self.controls:
            w = self.controls.pop(key)
            self.layout.removeWidget(w)
            w.deleteLater()

    def clear_all(self):
        for key in list(self.controls.keys()):
            self.clear(key)


@log_method_calls()
class ConfigWidget(CentralChildWidget):
    def __init__(self, parent=None):
        self.dynamic_manager: Optional[DynamicControlManager] = None
        self.settings = QSettings("ApiViewer", "ConfigWidget")
        self.state = ConfigState()
        super().__init__(parent)
        self.current_request_task: Optional[asyncio.Task] = None

    def _setup_ui(self):
        self.control_splitter = QSplitter(Qt.Orientation.Vertical)
        self.control_splitter.addWidget(self._build_controls_panel())
        self.control_splitter.addWidget(self._build_body_panel())
        self.layout().addWidget(self.control_splitter)

    def _build_controls_panel(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(*NO_MARGIN)
        self.dynamic_manager = DynamicControlManager(layout)
        self._add_generic_api_controls(layout)
        self._prodtest_checkbox = QCheckBox("Prodtest")
        layout.addWidget(self._prodtest_checkbox)
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        return w

    def _add_generic_api_controls(self, layout: QVBoxLayout):
        self.generic_api_controls: Dict[str, QComboBox] = {}
        for label in ["API", "Endpoint", "Client"]:
            cb = QComboBox()
            cb.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
            cb.setDuplicatesEnabled(False)
            cb.setMaxVisibleItems(10)
            cb.setMinimumContentsLength(20)
            self.generic_api_controls[label.lower()] = cb
            h = QHBoxLayout()
            h.setContentsMargins(*NO_MARGIN)
            h.addWidget(QLabel(f"{label}:"), 1)
            h.addWidget(cb, 3)
            layout.addLayout(h)

    def _build_body_panel(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(*NO_MARGIN)
        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(*NO_MARGIN)
        body_layout.addWidget(QLabel("Body:"), alignment=Qt.AlignmentFlag.AlignTop)

        self.text_edit = JsonTextEdit()
        self.text_edit.setFixedHeight(150)
        body_layout.addWidget(self.text_edit)

        # Progress and error
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        body_layout.addWidget(self.progress)
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red")
        self.error_label.setVisible(False)
        body_layout.addWidget(self.error_label)

        # Send button
        self.send_button = QPushButton("Send request")
        self.send_button.setFixedHeight(30)
        body_layout.addWidget(self.send_button)

        self.control_splitter.addWidget(body_widget)
        self.control_splitter.setStretchFactor(0, 1)
        self.control_splitter.setStretchFactor(1, 2)
        self.layout().addWidget(self.control_splitter)

        # Populate API combobox
        for name, spec in self.spec_registry.all().items():
            self.generic_api_controls["api"].addItem(name, spec)
        self.generic_api_controls["api"].setCurrentIndex(0)
        self.generic_api_controls["api"].setEnabled(True)
        self._on_api_change(0)

        return w

    def _connect_signals(self):
        self.generic_api_controls["api"].currentIndexChanged.connect(self._on_api_change)
        self.generic_api_controls["endpoint"].currentIndexChanged.connect(self._on_endpoint_change)
        self.generic_api_controls["client"].currentIndexChanged.connect(self._on_client_change)
        self._prodtest_checkbox.stateChanged.connect(self._on_prodtest_changed)

        self.text_edit.jsonValidityChanged.connect(self._on_json_validity_changed)
        self.text_edit.textChanged.connect(self._on_body_text_changed)

        self.send_button.clicked.connect(self._on_send_request)

    def _load_settings(self):
        logger.debug("Loading settings")
        idx = self.settings.value("apiIndex", 0, int)
        logger.debug(f"API index: {idx}")
        self.generic_api_controls["api"].setCurrentIndex(idx)
        logger.debug(f"API name: {self.generic_api_controls['api'].itemText(idx)}")
        # self.text_edit.setPlainText(self.settings.value("bodyText", ""))
        logger.debug(f"Body text: {self.text_edit.toPlainText()}")

    def _save_settings(self):
        self.settings.setValue("apiIndex", self.generic_api_controls["api"].currentIndex())
        self.settings.setValue("bodyText", self.text_edit.toPlainText())

    def _on_api_change(self, index: int) -> None:
        self._save_settings()
        spec = self.generic_api_controls["api"].itemData(index)
        self.state.api_spec = spec
        # reset downstream
        for key in ("endpoint", "client"): self.generic_api_controls[key].clear()
        self.dynamic_manager.clear_all()
        self.error_label.setVisible(False)

        paths = spec.get("paths", {})
        for path, p_spec in paths.items():
            self.generic_api_controls["endpoint"].addItem(path, p_spec)
        for name, c_spec in self.client_registry.all().items():
            self.generic_api_controls["client"].addItem(name, c_spec)

    def _on_endpoint_change(self, index: int) -> None:
        self.state.endpoint_path = self.generic_api_controls["endpoint"].currentText()

    def _on_client_change(self, index: int) -> None:
        self.dynamic_manager.clear_all()
        self.state.client_spec = self.generic_api_controls["client"].itemData(index)
        if self.generic_api_controls["api"].currentText() == "RGS_Decisioning":
            rules = self.state.client_spec.get("rulesetKeys", [])
            if rules:
                cb = QComboBox()
                for r in rules:
                    text = f"{r['country']}_{r['channel']}_{r['key']}"
                    cb.addItem(text, r)
                self.dynamic_manager.add("rulesetKey", cb)

    def _on_prodtest_changed(self, state: int) -> None:
        self.state.prodtest = (state == Qt.CheckState.Checked)

    def _on_json_validity_changed(self, is_valid: bool) -> None:
        self.send_button.setEnabled(is_valid)
        color = "white" if is_valid else "#ffeaea"
        self.text_edit.setStyleSheet(f"background-color: {color};")

    def _on_body_text_changed(self) -> None:
        if self.current_request_task and not self.current_request_task.done():
            self.current_request_task.cancel()
            self.error_label.setVisible(True)
            self.error_label.setText("Request canceled due to edit.")

    @asyncSlot()
    async def _on_send_request(self) -> None:
        if self.current_request_task and not self.current_request_task.done():
            return

        self.error_label.setVisible(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self._set_controls_enabled(False)

        self.current_request_task = asyncio.create_task(self._send_request_task())

    async def _send_request_task(self) -> None:
        try:
            body = self._gather_body()
            if self.state.prodtest:
                path = "/prodtest/" + self.state.endpoint_path.lstrip("/")
            else:
                path = self.state.endpoint_path
            await self.api_handler.call(
                self.state.api_spec, path, self.state.client_spec, body
            )
        except Exception as e:
            logger.exception("Request failed")
            self.error_label.setVisible(True)
            self.error_label.setText(f"Error: {e}")
        finally:
            self.progress.setVisible(False)
            self._set_controls_enabled(True)

    def _gather_body(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        # specific controls
        for key, w in self.dynamic_manager.controls.items():
            if isinstance(w, QComboBox):
                data[key] = w.currentData()
        # JSON body
        raw = self.text_edit.toPlainText()
        if raw.strip():
            data.update(json.loads(raw))
        return data

    def _set_controls_enabled(self, enable: bool) -> None:
        for w in self.generic_api_controls.values():
            w.setEnabled(enable)
        self._prodtest_checkbox.setEnabled(enable)
        for w in self.dynamic_manager.controls.values():
            w.setEnabled(enable)
        self.text_edit.setEnabled(enable)
        self.send_button.setEnabled(enable)
