from PyQt6.QtCore import QStringListModel
from PyQt6.QtWidgets import QListView

from src.central_widget.core import CentralChildWidget


class RequestWidget(CentralChildWidget):
    def _setup_viewer(self):
        self.viewer_model = QStringListModel(self)
        self.viewer_widget = QListView()

