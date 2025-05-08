from typing import overload, Dict, Any, Optional, Union

from PyQt6.QtCore import QStringListModel, Qt
from PyQt6.QtWidgets import QListView, QSplitter

from api_viewer.central_widget.core import CentralChildWidget, RequestResponseViewTabs
from api_viewer.constants import NO_MARGIN
from api_viewer.log.decorator import log_method_calls


@log_method_calls()
class RequestWidget(CentralChildWidget):
    def _setup_ui(self):
        # Create splitter
        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Orientation.Vertical)
        splitter.setContentsMargins(*NO_MARGIN)
        self.layout().addWidget(
            splitter
        )

        # Setup token request viewer
        self.token_request_widget = RequestResponseViewTabs(self, "Token Request:")
        splitter.addWidget(
            self.token_request_widget
        )

        # Setup token response viewer
        self.token_response_widget = RequestResponseViewTabs(self, "Token Response:")
        splitter.addWidget(
            self.token_response_widget
        )

        # Set up the request window
        self.viewer_widget = RequestResponseViewTabs(self, "Request:")

        splitter.addWidget(
            self.viewer_widget
        )

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 2)

    def _connect_signals(self):
        self.signals.loadRequestId.connect(self._load_request_id)

    def _load_request_id(self, req_id: int) -> None:
        """Load the request with the given ID."""
        # Load the request and response from the database
        request = self.storage.fetch_request(req_id)
        token_request = self.storage.fetch_request(request["token_request_id"])

        # Update the viewer with the loaded request and response
        self._update_content(self.viewer_widget, request.get("request_body"))

        if token_request:
            self._update_content(self.token_request_widget, token_request.get("request_body"))
            self._update_content(self.token_response_widget, token_request.get("response_body"))
