import asyncio
import json
import logging
from contextlib import contextmanager
from copy import deepcopy
from functools import lru_cache
from typing import Any, Callable, Dict, Optional

from PyQt6.QtGui import QFocusEvent
from qasync import asyncSlot
from PyQt6.QtCore import Qt, QSettings, QSignalBlocker, QTimer
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QComboBox,
    QLabel,
    QSplitter,
    QWidget,
    QCheckBox,
    QSizePolicy,
    QSpacerItem,
    QProgressBar, QMessageBox,
)

from api_viewer.central_widget.config_widget.api_interface import ApiServiceInterface, ApiService, ApiServiceError
from api_viewer.central_widget.config_widget.core import (
    ControlKey,
    ConfigState,
    UIFactory,
    DynamicControlManager, ControlType, ControlKeyType,
)
from api_viewer.central_widget.config_widget.settings import SettingsManager
from api_viewer.central_widget.core import CentralChildWidget
from api_viewer.constants import NO_MARGIN
from api_viewer.json_text_edit import JsonTextEdit
from api_viewer.log.decorator import log_method_calls

logger = logging.getLogger(__name__)

JsonDict = Dict[str, Any]

_BODY_LABEL       = "Body:"
_JSON_DELAY_MS   = 500
_SUCCESS_STYLE   = "color: green;"
_ERROR_STYLE     = "color: red;"
_INVALID_JSON_TXT= "Invalid JSON format."

# -----------------------------------------------------------------------------
# Helper: merge schemas
# -----------------------------------------------------------------------------

def _merge_schemas(base: JsonDict, override: JsonDict) -> JsonDict:
    result = deepcopy(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _merge_schemas(result[key], val)
        elif key in result and isinstance(result[key], list) and isinstance(val, list):
            result[key] = result[key] + [v for v in val if v not in result[key]]
        else:
            result[key] = deepcopy(val)
    return result


# -----------------------------------------------------------------------------
# Schema resolver for OpenAPI JSON schemas
# -----------------------------------------------------------------------------
class SchemaResolver:
    def __init__(self, api_spec: JsonDict) -> None:
        self.api_spec = api_spec

    def get_post_schema(self, endpoint_spec: JsonDict) -> Optional[JsonDict]:
        try:
            raw = endpoint_spec["post"]["requestBody"]["content"]["application/json"]["schema"]
        except KeyError:
            return None
        return self._resolve_refs(deepcopy(raw))

    def get_component_schema(self, component_name: str) -> Optional[JsonDict]:
        if not component_name:
            return None
        components = self.api_spec.get("components", {}).get("schemas", {})
        return components.get(component_name) or next(
            (deepcopy(s) for name, s in components.items() if name.endswith(component_name)),
            None,
        )

    def _resolve_refs(self, node: Any) -> Any:
        if isinstance(node, list):
            return [self._resolve_refs(item) for item in node]
        if isinstance(node, dict):
            if all_of := node.pop("allOf", []):
                merged = {}
                for subschema in all_of:
                    merged = _merge_schemas(merged, self._resolve_refs(subschema))
                return self._resolve_refs(_merge_schemas(merged, node))
            if ref := node.get("$ref"):
                if ref.startswith("#/components/schemas/"):
                    name = ref.rsplit("/", 1)[-1]
                    comp = self._get_cached_component(name)
                    return deepcopy(comp) if comp else {}
                return {}
            return {k: self._resolve_refs(v) for k, v in node.items()}
        return node

    @lru_cache(maxsize=None)
    def _get_cached_component(self, name: str) -> Optional[JsonDict]:
        raw = self.get_component_schema(name)
        return self._resolve_refs(raw) if raw else None


# -----------------------------------------------------------------------------
# Main configuration widget
# -----------------------------------------------------------------------------
@log_method_calls()
class ConfigWidget(CentralChildWidget):
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        settings: Optional[QSettings] = None,
        api_service: Optional[ApiServiceInterface] = None,
    ):
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
        self._load_settings()

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
        self.generic_controls = {
            key: UIFactory.widget(ControlKeyType[key.name].value, key.name.title(), layout)
            for key in ControlKey
        }
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        return panel

    def _make_body_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(*NO_MARGIN)
        layout.addWidget(QLabel(_BODY_LABEL), alignment=Qt.AlignmentFlag.AlignTop)

        self.text_edit = JsonTextEdit()
        self.text_edit.setTextChangeDelay(_JSON_DELAY_MS)
        layout.addWidget(self.text_edit)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.error_label = QLabel()
        self.error_label.setVisible(False)
        self.error_label.setStyleSheet(_ERROR_STYLE)
        layout.addWidget(self.error_label)

        self.send_button = UIFactory.button("Send request", layout)
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
        self.generic_controls[ControlKey.API].activated.connect(self._on_api_change)
        self.generic_controls[ControlKey.EXTERNAL].checkStateChanged.connect(self._on_external_toggle)
        self.generic_controls[ControlKey.ENDPOINT].activated.connect(
            lambda _: self.state.set_endpoint(self.generic_controls[ControlKey.ENDPOINT].currentText())
        )
        self.generic_controls[ControlKey.CLIENT].activated.connect(self._on_client_change)
        self.signals.dynamicControlUpdated.connect(self._refresh_body_template)
        self.text_edit.jsonValidityChanged.connect(self._on_json_validity)
        self.send_button.clicked.connect(self._on_send)
        self.signals.reloadBodyFromHistory.connect(self._on_reload_body_from_id)

    # -------------------------------------------------------------------------
    # Loading & Settings
    # -------------------------------------------------------------------------
    def _populate_apis(self, api) -> None:
        combo = self.generic_controls[ControlKey.API]
        combo.clear()
        for name, spec in self.spec_registry.all().items():
            combo.addItem(name, spec)

        idx = self.settings.load_index(ControlKey.API)
        with QSignalBlocker(combo):
            combo.setCurrentIndex(idx)

    def _load_settings(self) -> None:
        self.text_edit.setPlainText(self.settings.load_text("bodyText"))

    def _on_reload_body_from_id(self, req_id) -> None:
        request = self.storage.fetch_request(req_id)
        self.text_edit.setText(request.get("request_body"))
        self.text_edit.updateFormat()

    # -------------------------------------------------------------------------
    # Handlers
    # -------------------------------------------------------------------------
    def _on_api_change(self, index: int) -> None:
        api_name = self.generic_controls[ControlKey.API].currentText()
        if api_name not in self._resolvers:
            spec = self.generic_controls[ControlKey.API].itemData(index)
            self._resolvers[api_name] = SchemaResolver(spec)
        self._resolver = self._resolvers[api_name]
        spec = self._resolver.api_spec
        self.settings.save_index(ControlKey.API, self.generic_controls[ControlKey.API].currentIndex())
        self.state.set_api_spec(spec)
        self.dynamic_manager.clear_all()
        self.error_label.setVisible(False)
        client_items = self.client_registry.all() if self.generic_controls[ControlKey.EXTERNAL].checkState() == Qt.CheckState.Checked else self.client_registry.internal_clients()
        UIFactory.populate_combo(self.generic_controls[ControlKey.ENDPOINT], spec.get("paths", {}))
        self.state.endpoint_path = self.generic_controls[ControlKey.ENDPOINT].currentText()
        UIFactory.populate_combo(self.generic_controls[ControlKey.CLIENT], client_items)
        self.state.client_spec = self.generic_controls[ControlKey.CLIENT].currentData()
        self._refresh_body_template()

    def _on_external_toggle(self, state: int) -> None:
        # save setting
        self.settings.save_flag(ControlKey.EXTERNAL, state == Qt.CheckState.Checked)
        # re-populate clients based on new flag
        self._on_api_change(self.generic_controls[ControlKey.API].currentIndex())

    def _on_client_change(self, index: int) -> None:
        spec = self.generic_controls[ControlKey.CLIENT].itemData(index)
        if not spec.get("internalClient", False):
            answer = self._request_confirmation(spec)
            if not answer:
                return
        self.dynamic_manager.clear_all()
        self.state.client_spec = spec
        handler = self._dynamic_handlers.get(self.generic_controls[ControlKey.API].currentText())
        if handler:
            handler(spec)

    def _on_json_validity(self, is_valid: bool, _msg: str) -> None:
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

    # -------------------------------------------------------------------------
    # Dynamic body template
    # -------------------------------------------------------------------------
    def _refresh_body_template(self, *args) -> None:
        if self.user_changed_body:
            return
        endpoint_spec = self.generic_controls[ControlKey.ENDPOINT].currentData()
        if not endpoint_spec:
            self.text_edit.setPlainText("")
            return
        schema = self._resolver.get_post_schema(endpoint_spec)
        if schema and (req := schema.get("required", [])):
            template = {key: "" for key in req}
            self.text_edit.setPlainText(json.dumps(template, indent=2))

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
            combo = self.generic_controls[key]
            combo.clear()
            for name, data in (items.items() if isinstance(items, dict) else
                               ((getattr(i, 'name', str(i)), i) for i in items)):
                combo.addItem(name, data)

    def _set_all_enabled(self, on: bool) -> None:
        for ctrl in self.generic_controls.values():
            ctrl.setEnabled(on)
        self.dynamic_manager.set_all_enabled(on)
        self.send_button.setEnabled(on)

    def _request_confirmation(self, spec: JsonDict) -> bool:
        # Show a confirmation dialog to the user
        title = "Confirm external client usage"
        message = (
            f"Are you sure you want to use the external client '{spec.get('clientId')}' "
            f"for the API '{self.generic_controls[ControlKey.API].currentText()}'?"
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
