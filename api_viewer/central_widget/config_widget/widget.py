import asyncio
import json
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, Callable

from PyQt6.QtCore import QSettings, Qt, QTimer, QSignalBlocker
from PyQt6.QtWidgets import QWidget, QSplitter, QVBoxLayout, QSpacerItem, QSizePolicy, QLabel, QProgressBar, \
    QMessageBox, QComboBox
from PyQt6_JsonTextEdit import QJsonTextEdit
from httpx import URL
from qasync import asyncSlot

from api_viewer.central_widget.config_widget.api_service import ApiService
from api_viewer.central_widget.config_widget.dynamic_control_manager import DynamicControlManager
from api_viewer.central_widget.config_widget.exceptions import ApiServiceError
from api_viewer.central_widget.config_widget.interface import ApiServiceInterface
from api_viewer.central_widget.config_widget.schema_resolver import SchemaResolver
from api_viewer.central_widget.config_widget.setting_manager import SettingsManager
from api_viewer.central_widget.config_widget.state import ConfigState
from api_viewer.central_widget.config_widget.utils import _BODY_LABEL, _JSON_DELAY_MS, _SUCCESS_STYLE, _ERROR_STYLE, \
    _INVALID_JSON_TXT, ControlKey, ControlKeyType, JsonDict
from api_viewer.central_widget.core.central_child import CentralChildWidget
from api_viewer.constants import NO_MARGIN
from api_viewer.log.decorator import log_method_calls
from api_viewer.ui_helpers import add_labeled_row, populate_combo
from api_viewer.widget_factory import WidgetFactory

logger = logging.getLogger(__name__)

@log_method_calls()
class ConfigWidget(CentralChildWidget):
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        settings: Optional[QSettings] = None,
        api_service: Optional[ApiServiceInterface] = None,
    ):
        self.api_control_widget = None
        self.endpoint_control_widget = None
        self.client_control_widget = None
        self.prodtest_control_widget = None
        self.external_control_widget = None

        self._resolvers: Dict[str, SchemaResolver] = {}
        self.state = ConfigState()
        self._settings = settings or QSettings("ApiViewer", "ConfigWidget")
        self.settings = SettingsManager(self._settings)
        self.dynamic_manager: DynamicControlManager
        self.current_task: Optional[asyncio.Task] = None
        self.user_changed_body = False
        super().__init__(parent)
        self.api_service = api_service or ApiService(self.api_handler)

    # -------------------------------------------------------------------------
    # UI Setup
    # -------------------------------------------------------------------------
    def _setup_ui(self) -> None:
        self._init_layout()
        self._connect_signals()

    def _init_layout(self) -> None:
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.addWidget(self._make_control_panel())
        self.splitter.addWidget(self._make_body_panel())
        self.layout().addWidget(self.splitter)

    def _make_control_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(*NO_MARGIN)
        self.dynamic_manager = DynamicControlManager(layout)

        # generic controls
        for key in ControlKey:
            widget = WidgetFactory.widget(ControlKeyType[key.name].value)
            add_labeled_row(layout, key.name.title(), widget)
            widget_name = key.name.lower() + "_control_widget"
            setattr(self, widget_name, widget)
            if hasattr(widget, "activated"):
                widget.activated.connect(getattr(self, "_on_" + key.name.lower() + "_change"))

        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        return panel

    def _make_body_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(*NO_MARGIN)
        layout.addWidget(QLabel(_BODY_LABEL), alignment=Qt.AlignmentFlag.AlignTop)

        self.text_edit = QJsonTextEdit()
        self.text_edit.setTextChangeDelay(_JSON_DELAY_MS)
        layout.addWidget(self.text_edit)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.error_label = QLabel()
        self.error_label.setVisible(False)
        self.error_label.setStyleSheet(_ERROR_STYLE)
        layout.addWidget(self.error_label)

        self.send_button = WidgetFactory.button("Send request")
        layout.addWidget(self.send_button)
        return panel

    # -------------------------------------------------------------------------
    # Signals
    # -------------------------------------------------------------------------
    def _connect_signals(self) -> None:
        self._cancel_timer = QTimer(self)
        self._cancel_timer.setSingleShot(True)
        self.text_edit.textChanged.connect(lambda: self._cancel_timer.start(100))
        self._cancel_timer.timeout.connect(self._on_body_edit)

        self.signals.apiAvailable.connect(self._populate_apis)
        self.api_control_widget.activated.connect(self._on_api_change)
        self.external_control_widget.checkStateChanged.connect(self._on_external_toggle)
        self.endpoint_control_widget.activated.connect(
            lambda _: self.state.set_endpoint(self.endpoint_control_widget.currentText())
        )
        self.client_control_widget.activated.connect(self._on_client_change)
        self.signals.dynamicControlUpdated.connect(self._refresh_body_template)
        self.text_edit.jsonValidityChanged.connect(self._on_json_validity)
        self.send_button.clicked.connect(self._on_send)
        self.signals.reloadBodyFromHistory.connect(self._on_reload_body_from_id)

    # -------------------------------------------------------------------------
    # Loading & Settings
    # -------------------------------------------------------------------------
    def _populate_apis(self, api) -> None:
        combo = self.api_control_widget
        combo.clear()
        for name, spec in self.spec_registry.all().items():
            combo.addItem(name, spec)

        idx = self.settings.load_index(ControlKey.API)
        with QSignalBlocker(combo):
            combo.setCurrentIndex(idx)

    def _on_reload_body_from_id(self, req_id) -> None:
        request = self.storage.fetch_request(req_id)
        self.text_edit.setJson(request.get("request_body"))
        self.text_edit.updateFormat()

    # -------------------------------------------------------------------------
    # Handlers
    # -------------------------------------------------------------------------
    def _on_api_change(self, index: int) -> None:
        api_name = self.api_control_widget.currentText()
        if api_name not in self._resolvers:
            spec = self.api_control_widget.itemData(index)
            self._resolvers[api_name] = SchemaResolver(spec)
        self._resolver = self._resolvers[api_name]
        spec = self._resolver.api_spec
        self.settings.save_index(ControlKey.API, self.api_control_widget.currentIndex())
        self.state.set_api_spec(spec)
        self.dynamic_manager.clear_all()
        self.error_label.setVisible(False)

        host = URL(spec.get("servers")[0]["url"]).host

        if self.external_control_widget.checkState() == Qt.CheckState.Checked:
            client_items = self.client_registry.all(host)
        else:
            client_items = self.client_registry.internal_clients(host)

        populate_combo(self.endpoint_control_widget, spec.get("paths", {}))
        self.state.endpoint_path = self.endpoint_control_widget.currentText()
        populate_combo(self.client_control_widget, client_items)
        self.state.client_spec = self.client_control_widget.currentData()

        self._refresh_body_template()

    def _on_external_toggle(self, state: int) -> None:
        # save setting
        self.settings.save_flag(ControlKey.EXTERNAL, state == Qt.CheckState.Checked)
        # re-populate clients based on new flag
        self._on_api_change(self.api_control_widget.currentIndex())

    def _on_client_change(self, index: int) -> None:
        spec = self.client_control_widget.itemData(index)
        if not spec.get("internalClient", False):
            answer = self._request_confirmation(spec)
            if not answer:
                return
        self.dynamic_manager.clear_all()
        self.state.client_spec = spec
        handler = self._dynamic_handlers.get(self.api_control_widget.currentText())
        if handler:
            handler(spec)

    def _on_json_validity(self, is_valid: bool, _msg: str = "") -> None:
        self.send_button.setEnabled(is_valid)
        self.error_label.setVisible(not is_valid)
        if not is_valid:
            self.error_label.setText(_INVALID_JSON_TXT)

    def _on_body_edit(self) -> None:
        self.user_changed_body = True
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()
            self.error_label.setVisible(True)
            self.error_label.setText("Request canceled due to edit.")

    def _on_endpoint_change(self, index: int) -> None:
        self.state.endpoint_path = self.endpoint_control_widget.currentText()
        self._refresh_body_template()

    # -------------------------------------------------------------------------
    # Dynamic body template
    # -------------------------------------------------------------------------
    def _refresh_body_template(self, *args) -> None:
        if self.user_changed_body:
            return
        endpoint_spec = self.endpoint_control_widget.currentData()
        if not endpoint_spec:
            self.text_edit.setPlainText("")
            return
        schema = self._resolver.get_schema(endpoint_spec)
        if schema:
            required_fields = schema.get("required", [])
            possible_fields = list(schema.get("properties", {}).keys())

    # -------------------------------------------------------------------------
    # Request execution
    # -------------------------------------------------------------------------
    @asyncSlot()
    async def _on_send(self) -> None:
        with QSignalBlocker(self.send_button):
            if self.current_task and not self.current_task.done():
                return
            with self._request_context():
                self.current_task = asyncio.create_task(self._execute_request())


    @contextmanager
    def _request_context(self):
        self.error_label.setVisible(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self._set_all_enabled(False)
        yield

    async def _execute_request(self) -> None:
        exc = None
        try:
            payload = self._gather_body()
            if self.state.prodtest:
                path = "/prodtest/" + self.state.endpoint_path.lstrip("/")
            else:
                path = self.state.endpoint_path
            await self.api_service.call_api(
                self.state.api_spec, path, self.state.client_spec, payload
            )
        except asyncio.CancelledError:
            logger.info("Request was cancelled")
        except ApiServiceError as exc:
            self._show_error(f"API error: {exc}")
        except Exception as exc:
            logger.exception("Request failed")
            self.error_label.setVisible(True)
            self.error_label.setText(f"Error: {exc}")
        finally:
            self.progress_bar.setVisible(False)
            self._set_all_enabled(True)
            if not exc:
                self.error_label.setStyleSheet(_SUCCESS_STYLE)
                self.error_label.setText("✔ Request succeeded")
                QTimer.singleShot(1500, lambda: self.error_label.setVisible(False))

    def _show_error(self, message: str) -> None:
        self.error_label.setVisible(True)
        self.error_label.setText(message)
        self.error_label.setStyleSheet(_ERROR_STYLE)
        QTimer.singleShot(1500, lambda: self.error_label.setVisible(False))

    def _gather_body(self) -> Dict[str, Any]:
        body = {
            key: ctrl.currentData()
            for key, ctrl in self.dynamic_manager.controls.items()
        }
        raw = self.text_edit.toPlainText().strip()
        if raw:
            body.update(json.loads(raw))
        return body

    def _reset_and_populate(
        self,
        key1: ControlKey,
        items1: Any,
        key2: ControlKey,
        items2: Any,
    ) -> None:
        for key, items in ((key1, items1), (key2, items2)):
            combo = getattr(self, f"{key.name.lower()}_control_widget")
            combo.clear()
            for name, data in (items.items() if isinstance(items, dict) else
                               ((getattr(i, 'name', str(i)), i) for i in items)):
                combo.addItem(name, data)

    def _set_all_enabled(self, enabled: bool) -> None:
        self.api_control_widget.setEnabled(enabled)
        self.endpoint_control_widget.setEnabled(enabled)
        self.client_control_widget.setEnabled(enabled)
        self.prodtest_control_widget.setEnabled(enabled)
        self.external_control_widget.setEnabled(enabled)
        self.text_edit.setEnabled(enabled)
        self.send_button.setEnabled(enabled)

        self.dynamic_manager.set_all_enabled(enabled)

    def _request_confirmation(self, spec: JsonDict) -> bool:
        # Show a confirmation dialog to the user
        title = "Confirm external client usage"
        message = (
            f"Are you sure you want to use the external client '{spec.get('clientId')}' "
            f"for the API '{self.api_control_widget.currentText()}'?"
        )
        reply = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            return True
        else:
            # User clicked "No", do not proceed with the external client
            return False

    @property
    def _dynamic_handlers(self) -> Dict[str, Callable[[Any], None]]:
        return {"RGS_Decisioning": self._add_ruleset_control}

    def _add_ruleset_control(self, spec: Any) -> None:
        combo = QComboBox()
        for rule in spec.get("rulesetKeys", []):
            combo.addItem(f"{rule['country']}_{rule['channel']}_{rule['key']}", rule["key"])
        self.dynamic_manager.add("rulesetKey", combo)
