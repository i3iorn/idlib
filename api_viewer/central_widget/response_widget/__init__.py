import json
from PyQt6.QtCore import QStringListModel, Qt
from PyQt6.QtWidgets import (
    QTabWidget, QListView, QPlainTextEdit, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget
)

from api_viewer.central_widget.core import CentralChildWidget
from api_viewer.log.decorator import log_method_calls


@log_method_calls()
class ResponseWidget(CentralChildWidget):
    def _setup_ui(self):
        # Tabbed viewer
        self.tab_widget = QTabWidget()
        self.layout().addWidget(self.tab_widget)

        # Raw tab
        self.raw_model = QStringListModel(self)
        self.raw_view = QListView()
        self.raw_view.setModel(self.raw_model)
        self.tab_widget.addTab(self.raw_view, "Raw")

        # Pretty tab
        self.pretty_view = QPlainTextEdit()
        self.pretty_view.setReadOnly(True)
        self.tab_widget.addTab(self.pretty_view, "Pretty")

        # Paths tab
        self.paths_view = QTableWidget()
        self.paths_view.setColumnCount(2)
        self.paths_view.setHorizontalHeaderLabels(["Path", "Value"])
        self.paths_view.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.paths_view.horizontalHeader().setStretchLastSection(True)
        self.tab_widget.addTab(self.paths_view, "Paths")

    def _connect_signals(self):
        # Connect signals to methods
        self.signals.response.connect(self._update_response)

    def _update_response(self, response: str) -> None:
        self.raw_model.setStringList(response.splitlines())

        try:
            json_data = json.loads(response.splitlines()[-1])
        except (json.JSONDecodeError, TypeError):
            self.pretty_view.setPlainText("Invalid JSON")
            self.paths_view.setRowCount(0)
            return

        # Pretty print JSON
        pretty = json.dumps(json_data, indent=4, ensure_ascii=False)
        self.pretty_view.setPlainText(pretty)

        # Flatten and display in path-value table
        flat_items = self._flatten_json(json_data)
        self.paths_view.setRowCount(len(flat_items))
        for row, (path, value) in enumerate(flat_items.items()):
            self.paths_view.setItem(row, 0, QTableWidgetItem(path))
            self.paths_view.setItem(row, 1, QTableWidgetItem(str(value)))

    def _flatten_json(self, data, parent_key='', sep='.') -> dict:
        """Recursively flattens a JSON structure into a dict of paths to values."""
        items = {}
        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{parent_key}{sep}{key}" if parent_key else key
                items.update(self._flatten_json(value, full_key, sep))
        elif isinstance(data, list):
            for i, value in enumerate(data):
                full_key = f"{parent_key}[{i}]"
                items.update(self._flatten_json(value, full_key, sep))
        else:
            items[parent_key] = data
        return items
