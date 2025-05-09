from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QSpacerItem, QSizePolicy)

from api_viewer.central_widget.core import CentralChildWidget, RequestResponseViewTabs
from api_viewer.log.decorator import log_method_calls
from api_viewer.utils import response_dict_to_http_format


@log_method_calls()
class ResponseWidget(CentralChildWidget):
    def _setup_ui(self):
        # Request time
        self._setup_request_time_widget()
        self._setup_tabs()

    def _setup_request_time_widget(self):
        layout = QHBoxLayout()
        label = QLabel("Request time: ")
        self.request_time_value = QLabel("0")
        self.request_time_unit = QLabel("ms")

        layout.addStretch()
        layout.addWidget(label)
        layout.addWidget(self.request_time_value)
        layout.addWidget(self.request_time_unit)
        layout.addItem(
            QSpacerItem(20, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        )
        self.layout().addLayout(layout)

    def _setup_tabs(self):
        # Tabbed viewer
        self.tab_widget = RequestResponseViewTabs(self, "Response:")
        self.layout().addWidget(self.tab_widget)

    def _connect_signals(self):
        # Connect signals to methods
        self.signals.loadRequestId.connect(self._load_request_id)

    def _load_request_id(self, req_id: int) -> None:
        """Load the request with the given ID."""
        # Load the request and response from the database
        response = self.storage.fetch_response(req_id)
        self.set_request_time(response.get("response_time"))

        # Update the viewer with the loaded request and response
        self._update_content(self.tab_widget, response_dict_to_http_format(**response))

    def set_request_time(self, ns: float) -> None:
        """Set the request time in milliseconds."""
        if ns is None:
            raise ValueError("Request time cannot be None")
        if ns < 0:
            raise ValueError("Request time cannot be negative")

        request_time = ns

        units = {
            "ms": 1000,
            "s": 1000,
            "min": 60,
            "h": 60
        }
        unit = "ns"
        for u, factor in units.items():
            if request_time < factor: break
            unit = u
            request_time /= factor

        self.request_time_value.setText(f"{request_time:.2f}")
        self.request_time_unit.setText(unit)
