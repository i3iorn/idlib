import asyncio
import json
import logging
from contextlib import contextmanager
from typing import Dict, Any, Optional, Callable

from qasync import asyncSlot
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QComboBox,
    QLabel,
    QSplitter,
    QWidget,
    QCheckBox,
    QSizePolicy,
    QSpacerItem,
    QProgressBar,
)

from api_viewer.central_widget.config_widget.api_interface import ApiServiceInterface, ApiService
from api_viewer.central_widget.config_widget.core import ControlKey, ConfigState, UIFactory, DynamicControlManager
from api_viewer.central_widget.config_widget.settings import SettingsManager

from api_viewer.central_widget.core import CentralChildWidget
from api_viewer.constants import NO_MARGIN
from api_viewer.json_text_edit import JsonTextEdit
from api_viewer.log.decorator import log_method_calls

logger = logging.getLogger(__name__)

from copy import deepcopy
from functools import lru_cache
from typing import Any, Dict, Optional, Union

JsonDict = Dict[str, Any]


def _merge_schemas(base: JsonDict, override: JsonDict) -> JsonDict:
    """
    Deep-merge two schema dicts, combining properties and lists.
    """
    result = deepcopy(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _merge_schemas(result[key], val)
        elif key in result and isinstance(result[key], list) and isinstance(val, list):
            # combine lists uniquely
            combined = result[key] + [v for v in val if v not in result[key]]
            result[key] = combined
        else:
            result[key] = deepcopy(val)
    return result


class SchemaResolver:
    """
    Helper to extract and fully resolve JSON schemas (including internal $refs and allOf)
    from an OpenAPI spec loaded into Python dicts.
    """
    def __init__(self, api_spec: JsonDict) -> None:
        self.api_spec = api_spec

    def get_post_schema(self, endpoint_spec: JsonDict) -> Optional[JsonDict]:
        try:
            raw = (
                endpoint_spec["post"]["requestBody"]["content"]
                ["application/json"]["schema"]
            )
        except KeyError:
            return None

        schema_copy = deepcopy(raw)
        return self._resolve_refs(schema_copy)

    def get_component_schema(self, component_name: str) -> Optional[JsonDict]:
        if not component_name:
            return None
        components = self.api_spec.get("components", {}).get("schemas", {})
        if component_name in components:
            return deepcopy(components[component_name])
        for name, schema in components.items():
            if name.endswith(component_name):
                return deepcopy(schema)
        return None

    def _resolve_refs(self, node: Any) -> Any:
        """
        Recursively resolve $ref and allOf in the node.
        """
        # resolve lists
        if isinstance(node, list):
            return [self._resolve_refs(item) for item in node]

        # resolve dicts
        if isinstance(node, dict):
            # handle allOf merging
            if "allOf" in node and isinstance(node["allOf"], list):
                merged: JsonDict = {}
                for subschema in node.pop("allOf"):
                    resolved = self._resolve_refs(subschema)
                    if isinstance(resolved, dict):
                        merged = _merge_schemas(merged, resolved)
                # merge remaining keys in node
                merged = _merge_schemas(merged, node)
                return self._resolve_refs(merged)

            # handle direct $ref
            if "$ref" in node and isinstance(node["$ref"], str):
                ref = node["$ref"]
                if ref.startswith("#/components/schemas/"):
                    name = ref.split("/")[-1]
                    comp = self._get_cached_component(name)
                    return deepcopy(comp) if comp is not None else {}
                return {}

            # resolve other keys
            result: JsonDict = {}
            for key, val in node.items():
                result[key] = self._resolve_refs(val)
            return result

        # primitives
        return node

    @lru_cache(maxsize=None)
    def _get_cached_component(self, component_name: str) -> Optional[JsonDict]:
        raw = self.get_component_schema(component_name)
        return self._resolve_refs(raw) if raw is not None else None




@log_method_calls()
class ConfigWidget(CentralChildWidget):
    def __init__(self, parent=None, settings: Optional[QSettings] = None, api_service: Optional[
        ApiServiceInterface] = None):
        self._settings = settings or QSettings("ApiViewer", "ConfigWidget")
        self.settings = SettingsManager(self._settings)
        self.state = ConfigState()
        self.dynamic_manager: DynamicControlManager
        self.current_task: Optional[asyncio.Task] = None
        super().__init__(parent)
        self.api_service = api_service or ApiService(self.api_handler)

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
        self.generic_controls: Dict[ControlKey, QComboBox] = {
            key: UIFactory.combo(key.name.title(), layout) for key in ControlKey
        }
        self.prodtest_checkbox = QCheckBox("Prodtest")
        layout.addWidget(self.prodtest_checkbox)
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        return panel

    def _load_apis(self, event) -> None:
        self.generic_controls[ControlKey.API].clear()
        for api, spec in self.spec_registry.all().items():
            self.generic_controls[ControlKey.API].addItem(api, spec)
        self.generic_controls[ControlKey.API].setCurrentIndex(0)
        self._on_api_change(0)

    def _make_body_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(*NO_MARGIN)
        layout.addWidget(QLabel("Body:"), alignment=Qt.AlignmentFlag.AlignTop)
        self.text_edit = JsonTextEdit()
        self.text_edit.setTextChangeDelay(500)
        layout.addWidget(self.text_edit)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        self.error_label = QLabel()
        self.error_label.setVisible(False)
        self.error_label.setStyleSheet("color: red")
        layout.addWidget(self.error_label)
        self.send_button = UIFactory.button("Send request")
        layout.addWidget(self.send_button)
        return panel

    def _connect_signals(self) -> None:
        self.signals.api_available.connect(self._load_apis)
        self.generic_controls[ControlKey.API].activated.connect(self._on_api_change)
        self.generic_controls[ControlKey.ENDPOINT].activated.connect(self._on_endpoint_change)
        self.generic_controls[ControlKey.CLIENT].activated.connect(self._on_client_change)
        self.prodtest_checkbox.stateChanged.connect(
            lambda s: setattr(self.state, 'prodtest', s == Qt.Checked)
        )
        self.text_edit.jsonValidityChanged.connect(self._on_json_validity)
        self.text_edit.textChanged.connect(self._on_body_edit)
        self.send_button.clicked.connect(self._on_send)

    def _load_settings(self) -> None:
        idx = self.settings.load_index(ControlKey.API)
        self.generic_controls[ControlKey.API].setCurrentIndex(idx)
        self.text_edit.setPlainText(self.settings.load_text("bodyText"))

    def _save_settings(self) -> None:
        self.settings.save_index(ControlKey.API, self.generic_controls[ControlKey.API].currentIndex())
        self.settings.save_text("bodyText", self.text_edit.toPlainText())

    def _on_api_change(self, index: int) -> None:
        self._save_settings()
        spec = self.generic_controls[ControlKey.API].itemData(index)
        self.state.api_spec = spec
        self._reset_generic_controls(ControlKey.ENDPOINT, ControlKey.CLIENT)
        self.dynamic_manager.clear_all()
        self.error_label.setVisible(False)

        if spec is not None:
            self._populate(self.generic_controls[ControlKey.ENDPOINT], spec.get("paths", {}))

        if len(self.client_registry.all()) > 0:
            self._populate(self.generic_controls[ControlKey.CLIENT], self.client_registry.all())

    def _on_endpoint_change(self, _: int) -> None:
        self.state.endpoint_path = self.generic_controls[ControlKey.ENDPOINT].currentText()
        endpoint_spec = self.generic_controls[ControlKey.ENDPOINT].currentData()
        required_parameters = SchemaResolver(self.generic_controls[ControlKey.API].currentData()).get_post_schema(endpoint_spec)
        if required_parameters:
            missing = set(required_parameters.get("required")) - set(self.dynamic_manager.keys())
            # Create a body that contains all required parameters
            body = {}
            for param in missing:
                body[param] = ""

            self.text_edit.setPlainText(json.dumps(body, indent=2))

    def _on_client_change(self, _: int) -> None:
        self.dynamic_manager.clear_all()
        spec = self.generic_controls[ControlKey.CLIENT].currentData()
        self.state.client_spec = spec
        if handler := self._dynamic_handler_map.get(self.generic_controls[ControlKey.API].currentText()):
            handler(spec)

    @property
    def _dynamic_handler_map(self) -> Dict[str, Callable[[Any], None]]:
        return {"RGS_Decisioning": self._add_ruleset_control}

    def _add_ruleset_control(self, spec: Any) -> None:
        combo = QComboBox()
        if spec is not None:
            for rule in spec.get("rulesetKeys", []):
                combo.addItem(f"{rule['country']}_{rule['channel']}_{rule['key']}", rule)
        self.dynamic_manager.add("rulesetKey", combo)

    def _reset_generic_controls(self, *keys: ControlKey) -> None:
        for key in keys:
            self.generic_controls[key].clear()

    def _populate(self, combo: QComboBox, items: Any) -> None:
        if isinstance(items, dict):
            iter_items = items.items()
        else:
            iter_items = ((getattr(item, 'name', str(item)), item) for item in items)
        for name, item in iter_items:
            combo.addItem(name, item)

    def _on_json_validity(self, valid: bool, msg: str) -> None:
        self.send_button.setEnabled(valid)
        if not valid:
            self.error_label.setVisible(True)
            self.error_label.setText("Invalid JSON format.")
        else:
            self.error_label.setVisible(False)
            self.error_label.setText("")

    def _on_body_edit(self) -> None:
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()
            self.error_label.setVisible(True)
            self.error_label.setText("Request canceled due to edit.")

    @asyncSlot()
    async def _on_send(self) -> None:
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
        try:
            yield
        finally:
            # cleanup handled in _execute_request
            pass

    async def _execute_request(self) -> None:
        try:
            payload = self._gather_body()
            if self.state.prodtest:
                path = f"{'/prodtest/'}{self.state.endpoint_path.lstrip('/')}"
            else:
                path = self.state.endpoint_path

            await self.api_service.call_api(self.state.api_spec, path, self.state.client_spec, payload)
        except Exception as exc:
            logger.exception("Request failed")
            self.error_label.setVisible(True)
            self.error_label.setText(f"Error: {exc}")
        finally:
            self.progress_bar.setVisible(False)
            self._set_all_enabled(True)

    def _gather_body(self) -> Dict[str, Any]:
        body = {key: ctrl.currentData() for key, ctrl in self.dynamic_manager.controls.items()}
        raw = self.text_edit.toPlainText().strip()
        if raw:
            body.update(json.loads(raw))
        return body

    def _set_all_enabled(self, enabled: bool) -> None:
        for combo in self.generic_controls.values():
            combo.setEnabled(enabled)
        self.prodtest_checkbox.setEnabled(enabled)
        for ctrl in self.dynamic_manager.controls.values():
            ctrl.setEnabled(enabled)
        self.text_edit.setEnabled(enabled)
        self.send_button.setEnabled(enabled)
