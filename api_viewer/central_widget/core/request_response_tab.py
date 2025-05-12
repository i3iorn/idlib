import json
import logging
from typing import Optional, Any, Iterator, Tuple

from PyQt6.QtGui import QStandardItem
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy, QTabWidget, QListView, QTreeView, QTableView
from PyQt6_JsonTextEdit import QJsonTreeView, QJsonModel

from api_viewer.central_widget.core.view_tab import ViewTab

logger = logging.getLogger(__name__)


class RequestResponseViewTabs(QWidget):
    """
    Main composite widget with Raw, Pretty, Tree, and Paths tabs.
    """
    def __init__(self, parent=None, header: str = None):
        super().__init__(parent)
        logger.debug("Initializing RequestResponseViewTabs")
        self._model = QJsonModel(self)
        self._setup_ui(header)

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, value: QJsonModel):
        if not isinstance(value, QJsonModel):
            raise ValueError("Model must be an instance of QJsonModel")
        self._model = value

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
        self.raw_view = QListView()
        self.raw_view.setModel(self.model)
        tab = ViewTab(self.raw_view, self.model)
        self.tabs.addTab(tab, "Raw")

    def _make_pretty_tab(self):
        self.pretty_view = QJsonTreeView()
        tab = ViewTab(self.pretty_view, self.model)
        self.tabs.addTab(tab, "Pretty")

    def _make_tree_tab(self):
        view = QTreeView()
        view.setModel(self.model)
        view.header().setStretchLastSection(True)
        self.tree_view = view
        tab = ViewTab(view, self.model)
        self.tabs.addTab(tab, "Tree")

    def _make_paths_tab(self):
        self.model.setHorizontalHeaderLabels(["Path", "Value"])
        self.paths_view = QTableView()
        self.paths_view.setModel(self.model)
        self.paths_view.horizontalHeader().setStretchLastSection(True)
        tab = ViewTab(self.paths_view, self.model)
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
            self.model.setStringList(lines)
            try:
                data = json.loads(lines[-1].strip())
            except json.JSONDecodeError:
                logger.warning("Invalid JSON—switching to Raw")
                self.tabs.setCurrentIndex(0)
                self.raw_view.setEnabled(True)

                self.tree_view.setDisabled(True)
                self.pretty_view.setDisabled(True)
                self.paths_view.setDisabled(True)
                return
        elif dict_response is not None:
            self.raw_view.setDisabled(True)
            data = dict_response
        else:
            raise ValueError("Either http_response or dict_response must be provided")

        # Pretty
        try:
            pretty = json.dumps(data, indent=4, ensure_ascii=False)
            self.model.load_json(pretty)
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

        # Tree
        self._populate_tree(data)

        # Paths
        self._populate_paths(data)

    def _populate_tree(self, data: Any):
        self.model.removeRows(0, self.model.rowCount())
        self._recurse_tree(self.model.invisibleRootItem(), data)
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
        self.model.removeRows(0, self.model.rowCount())
        for path, val in self._walk_paths(data):
            path_item = QStandardItem(path)
            val_item = QStandardItem(str(val))
            self.model.appendRow([path_item, val_item])

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
