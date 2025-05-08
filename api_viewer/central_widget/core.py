import json
import logging
import os
from typing import List, Iterator, Any, Tuple, Optional, overload, Dict

import dotenv
from PyQt6.QtCore import QStringListModel, QSortFilterProxyModel, Qt, QAbstractItemModel, QModelIndex
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import QWidget, QSizePolicy, QVBoxLayout, QTabWidget, QListView, QTreeView, \
    QLabel, QLineEdit, QTableView, QHBoxLayout, QAbstractItemView

from bitwarden_secrets_manager_python import BWS

from api_viewer.api import SpecRegistry, ClientRegistry
from api_viewer.api.request_handler import APIRequestHandler
from api_viewer.constants import NO_MARGIN
from api_viewer.emitter import signal_emitter
from api_viewer.json_text_edit import JsonTextEdit
from api_viewer.log.decorator import log_method_calls
from api_viewer.storage import RequestResponseStorage

dotenv.load_dotenv()
logger =  logging.getLogger(__name__)


@log_method_calls()
class CentralChildWidget(QWidget):
    def __init__(self, parent=None, layout=None):
        super().__init__(parent)
        logger.debug(f"Initializing {self.__class__.__name__} with parent: {parent.__class__.__name__}")

        self.storage = RequestResponseStorage()
        self.spec_registry = SpecRegistry()
        self.client_registry = ClientRegistry()
        self.secrets_manager = BWS(
            bws_access_token=os.getenv("BWS_ACCESS_TOKEN"),
            cache_duration=os.getenv("BWS_CACHE_DURATION", 600),
            bws_path=os.getenv("BWS_PATH", "../bws.exe"),
        )
        logger.debug(f"Initialized secrets manager: {self.secrets_manager.__class__.__name__}")

        self.signals = signal_emitter

        self.api_handler = APIRequestHandler(self.secrets_manager, self.signals)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setObjectName(self.__class__.__name__)
        if layout is None:
            layout = QVBoxLayout()
        layout.setContentsMargins(*NO_MARGIN)
        self.setLayout(layout)

        if hasattr(self, "_setup_ui"):
            self._setup_ui()

        if hasattr(self, "_connect_signals"):
            self._connect_signals()

        if hasattr(self, "_load_settings"):
            self._load_settings()

        logger.debug(f"Finished initializing {self.__class__.__name__}")

    @overload
    def _update_content(self, widget, body: Optional[Dict[str, Any]] = None) -> None:...
    @overload
    def _update_content(self, widget, request: Optional[str] = None) -> None:...
    def _update_content(self, widget, body: Optional[Dict[str, Any]] = None, request: Optional[str] = None) -> None:
        data = request or body
        widget.update_content(data)


# ——— Helper to unwrap proxy models —————————————————————————————
def _unwrap_model(model: QAbstractItemModel) -> QAbstractItemModel:
    """
    If `model` is a QSortFilterProxyModel, return its sourceModel(),
    otherwise return it unchanged.
    """
    if isinstance(model, QSortFilterProxyModel):
        return model.sourceModel()
    return model


# ——— FilterBar ——————————————————————————————————————————————————
class FilterBar(QLineEdit):
    """
    A line edit that filters rows in any QAbstractItemView via
    a QSortFilterProxyModel.
    """
    def __init__(self, target_view: QAbstractItemView, placeholder: str = "Filter...", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self._view = target_view
        self._proxy = QSortFilterProxyModel(self)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.textChanged.connect(self._proxy.setFilterFixedString)
        self._reset_proxy()

    def _reset_proxy(self) -> None:
        source = _unwrap_model(self._view.model())
        self._proxy.setSourceModel(source)
        self._view.setModel(self._proxy)

    def update_model(self, new_model: QAbstractItemModel) -> None:
        """
        Call this if the underlying source model changes completely.
        """
        self._proxy.setSourceModel(new_model)
        self._view.setModel(self._proxy)


# ——— SearchBar ——————————————————————————————————————————————————
class SearchBar(QWidget):
    """
    A search widget with previous/next buttons that walks the
    underlying model to highlight matches without hiding rows.
    """
    def __init__(self, view: QAbstractItemView, placeholder: str = "Search...", parent=None):
        super().__init__(parent)
        self._view = view
        self._line = QLineEdit()
        self._line.setPlaceholderText(placeholder)
        self._prev_btn = QLabel("↑")
        self._next_btn = QLabel("↓")

        # clickable labels hack
        self._prev_btn.mousePressEvent = lambda _: self._prev_match()
        self._next_btn.mousePressEvent = lambda _: self._next_match()
        self._line.textChanged.connect(self._on_search)

        self._results: List[QModelIndex] = []
        self._idx = -1

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        for w in (self._line, self._prev_btn, self._next_btn):
            layout.addWidget(w)

    def _on_search(self, text: str) -> None:
        self._results.clear()
        self._idx = -1
        if not text:
            return

        model = _unwrap_model(self._view.model())
        self._results = [
            idx
            for idx in self._iter_all_indices(model)
            if text.lower() in str(model.data(idx, Qt.ItemDataRole.DisplayRole)).lower()
        ]
        if self._results:
            self._idx = 0
            self._highlight_current()

    def _iter_all_indices(self, model: QAbstractItemModel) -> Iterator[QModelIndex]:
        """
        Yield every index in a simple row-major traversal.
        """
        rows = model.rowCount()
        cols = model.columnCount()
        for r in range(rows):
            for c in range(cols):
                yield model.index(r, c)

    def _highlight_current(self) -> None:
        idx = self._results[self._idx]
        self._view.scrollTo(idx, self._view.ScrollHint.PositionAtCenter)
        self._view.setCurrentIndex(idx)

    def _next_match(self) -> None:
        if not self._results:
            return
        self._idx = (self._idx + 1) % len(self._results)
        self._highlight_current()

    def _prev_match(self) -> None:
        if not self._results:
            return
        self._idx = (self._idx - 1) % len(self._results)
        self._highlight_current()


# ——— ViewTab —————————————————————————————————————————————————
class ViewTab(QWidget):
    """
    Combines a view, its model, a SearchBar, and a FilterBar.
    """
    def __init__(
        self,
        view: QAbstractItemView,
        model: QAbstractItemModel,
        enable_search: bool = True,
        enable_filter: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.view = view
        self.model = model

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # control bars
        ctrl = QHBoxLayout()
        ctrl.setContentsMargins(0, 0, 0, 0)
        if enable_search:
            self.search = SearchBar(view)
            ctrl.addWidget(self.search)
        if enable_filter:
            self.filter = FilterBar(view)
            self.filter.update_model(model)
            ctrl.addWidget(self.filter)
        layout.addLayout(ctrl)
        layout.addWidget(view)


# ——— Main Tab Widget ————————————————————————————————————————————
class RequestResponseViewTabs(QWidget):
    """
    Main composite widget with Raw, Pretty, Tree, and Paths tabs.
    """
    def __init__(self, parent=None, header: str = None):
        super().__init__(parent)
        logger.debug("Initializing RequestResponseViewTabs")
        self._setup_ui(header)

    def _setup_ui(self, header: str | None):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        if header:
            lbl = QLabel(header)
            lbl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            outer.addWidget(lbl)

        self.tabs = QTabWidget()
        outer.addWidget(self.tabs)

        # build each tab
        self._make_raw_tab()
        self._make_pretty_tab()
        self._make_tree_tab()
        self._make_paths_tab()

        self.tabs.setCurrentIndex(1)  # default to Pretty

    def _make_raw_tab(self):
        self.raw_model = QStringListModel(self)
        self.raw_view = QListView()
        self.raw_view.setModel(self.raw_model)
        tab = ViewTab(self.raw_view, self.raw_model)
        self.tabs.addTab(tab, "Raw")

    def _make_pretty_tab(self):
        view = JsonTextEdit(read_only=True)
        # initially empty—set via update_content
        self.pretty_model = view.model()
        tab = ViewTab(view, self.pretty_model)
        self.pretty_view = view
        self.tabs.addTab(tab, "Pretty")

    def _make_tree_tab(self):
        model = QStandardItemModel(self)
        model.setHorizontalHeaderLabels(["Key", "Value"])
        view = QTreeView()
        view.setModel(model)
        view.header().setStretchLastSection(True)
        self.tree_model = model
        self.tree_view = view
        tab = ViewTab(view, model)
        self.tabs.addTab(tab, "Tree")

    def _make_paths_tab(self):
        model = QStandardItemModel(self)
        model.setHorizontalHeaderLabels(["Path", "Value"])
        self.paths_view = QTableView()
        self.paths_view.setModel(model)
        self.paths_view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.paths_view.horizontalHeader().setStretchLastSection(True)
        self.paths_model = model
        tab = ViewTab(self.paths_view, model)
        self.tabs.addTab(tab, "Paths")

    def update_content(self, http_response: Optional[str] = None, dict_response: Optional[dict] = None) -> None:
        """
        Feed a raw JSON/text response into all tabs.
        """
        if http_response is None and dict_response is None:
            raise ValueError("Either http_response or dict_response must be provided")

        if http_response is not None:
            # Raw
            self.raw_view.setEnabled(True)
            lines = http_response.splitlines()
            self.raw_model.setStringList(lines)
            data = json.loads(lines[-1].strip())
        elif dict_response is not None:
            self.raw_view.setDisabled(True)
            data = dict_response
        else:
            raise ValueError("Either http_response or dict_response must be provided")

        # Pretty
        try:

            self.tree_view.setEnabled(True)
            self.pretty_view.setEnabled(True)
            self.paths_view.setEnabled(True)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON—switching to Raw")
            self.tabs.setCurrentIndex(0)
            self.tree_view.setDisabled(True)
            self.pretty_view.setDisabled(True)
            self.paths_view.setDisabled(True)
            return

        pretty = json.dumps(data, indent=4, ensure_ascii=False)
        self.pretty_view.setPlainText(pretty)
        self.pretty_model = self.pretty_view.model()

        # Tree
        self._populate_tree(data)

        # Paths
        self._populate_paths(data)

    def _populate_tree(self, data: Any):
        self.tree_model.removeRows(0, self.tree_model.rowCount())
        self._recurse_tree(self.tree_model.invisibleRootItem(), data)
        self.tree_view.expandToDepth(1)

    def _recurse_tree(self, parent: QStandardItem, value: Any):
        if isinstance(value, dict):
            for k, v in value.items():
                key_item = QStandardItem(str(k))
                val_item = QStandardItem("" if isinstance(v, (dict, list)) else str(v))
                parent.appendRow([key_item, val_item])
                if isinstance(v, (dict, list)):
                    self._recurse_tree(key_item, v)
        elif isinstance(value, list):
            for i, v in enumerate(value):
                key_item = QStandardItem(f"[{i}]")
                val_item = QStandardItem("" if isinstance(v, (dict, list)) else str(v))
                parent.appendRow([key_item, val_item])
                if isinstance(v, (dict, list)):
                    self._recurse_tree(key_item, v)

    def _populate_paths(self, data: Any):
        self.paths_model.removeRows(0, self.paths_model.rowCount())
        for path, val in self._walk_paths(data):
            path_item = QStandardItem(path)
            val_item = QStandardItem(str(val))
            self.paths_model.appendRow([path_item, val_item])

    def _walk_paths(self, obj: Any, prefix: str = "") -> Iterator[Tuple[str, Any]]:
        if isinstance(obj, dict):
            for k, v in obj.items():
                new = f"{prefix}.{k}" if prefix else k
                yield from self._walk_paths(v, new)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                new = f"{prefix}[{i}]"
                yield from self._walk_paths(v, new)
        else:
            yield prefix, obj
