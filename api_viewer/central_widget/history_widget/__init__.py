from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel
from PyQt6.QtWidgets import QListView, QTableView, QMenu

from api_viewer.central_widget.core import CentralChildWidget
from api_viewer.storage import RequestResponseStorage


class HistoryWidget(CentralChildWidget):
    def _setup_ui(self):
        # Create the list view
        self.list_view = QTableView(self)
        self.model = QStandardItemModel()
        self.model.setColumnCount(2)
        self.model.setHorizontalHeaderLabels(["Status", "Endpoint"])
        self.list_view.setModel(self.model)
        self.list_view.setSortingEnabled(True)

        self.list_view.setColumnWidth(0, 40)
        self.list_view.setColumnWidth(1, 100)
        self.list_view.setAlternatingRowColors(True)
        self.layout().addWidget(self.list_view)

        # Set the view to be read-only
        self.list_view.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self.list_view.horizontalHeader().setStretchLastSection(True)
        self.list_view.setSelectionMode(QListView.SelectionMode.SingleSelection)

    def _connect_signals(self):
        self.signals.loadRequestId.connect(self._update_history)
        self.list_view.clicked.connect(self._on_item_clicked)

    def _load_settings(self):
        storage = RequestResponseStorage()
        for item in storage.fetch_all():
            if item.get("token_request_id") is not None:
                row = self.model.rowCount()
                self.model.insertRow(row)
                self.model.setData(self.model.index(row, 0), item["status_code"], role=Qt.ItemDataRole.DisplayRole)
                self.model.setData(self.model.index(row, 0), Qt.AlignmentFlag.AlignCenter, role=Qt.ItemDataRole.TextAlignmentRole)
                self.model.setData(self.model.index(row, 1), item["url"], role=Qt.ItemDataRole.DisplayRole)
                for column in range(2):
                    self.model.setData(self.model.index(row, column), item["request_id"], role=Qt.ItemDataRole.BackgroundRole)

    def _update_history(self, req_id) -> None:
        # Clear the current model
        self.model.removeRows(0, self.model.rowCount())
        self._load_settings()

    def _on_item_clicked(self, index):
        # Get the selected item
        item = self.model.itemFromIndex(index)
        if item is not None:
            # Get the row and column of the selected item
            row = item.row()
            column = item.column()

            # Get the data from the model
            request_id = self.model.item(row, column).data(Qt.ItemDataRole.BackgroundRole)
            if request_id is not None:
                # Do something with the data
                self.signals.loadRequestId.emit(request_id)
                self.signals.reloadBodyFromHistory.emit(request_id)