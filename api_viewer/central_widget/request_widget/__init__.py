from PyQt6.QtCore import QStringListModel
from PyQt6.QtWidgets import QListView

from api_viewer.central_widget.core import CentralChildWidget
from api_viewer.log.decorator import log_method_calls


@log_method_calls()
class RequestWidget(CentralChildWidget):
    def _setup_ui(self):
        self.viewer_model = QStringListModel(self)
        self.viewer_widget = QListView()
        self.viewer_widget.setModel(self.viewer_model)

        self.layout().addWidget(
            self.viewer_widget
        )

    def _connect_signals(self):
        self.signals.request.connect(self._update_request)

    def _update_request(self, request) -> None:
        self.viewer_model.setStringList(
            request.splitlines()
        )

