from PyQt6.QtCore import QStringListModel
from PyQt6.QtWidgets import QListView

from api_viewer.central_widget.core import CentralChildWidget


class ResponseWidget(CentralChildWidget):
    def _setup_viewer(self):
        self.viewer_model = QStringListModel(self)
        self.viewer_widget = QListView()
        self.viewer_widget.setModel(self.viewer_model)

        self.layout().addWidget(
            self.viewer_widget
        )