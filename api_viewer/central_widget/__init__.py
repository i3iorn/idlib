from PyQt6.QtWidgets import QWidget, QHBoxLayout

from src.constants import NO_MARGIN
from src.central_widget.config_widget import ConfigWidget
from src.central_widget.request_widget import RequestWidget
from src.central_widget.response_widget import ResponseWidget


class CentralWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        # Set up the main layout (Vertical)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(*NO_MARGIN)
        self._setup_conf_section(main_layout)
        self._setup_request_section(main_layout)
        self._setup_response_section(main_layout)

        # Add the horizontal layout to the main layout
        main_layout.addLayout(main_layout)

    def _setup_conf_section(self, main_layout):
        # Create the combo boxes and add them to the layout
        conf_widget = ConfigWidget(self)
        main_layout.addWidget(conf_widget)

    def _setup_request_section(self, main_layout):
        # Create two empty widgets
        self.request_widget = RequestWidget(self)
        # Add the empty widgets to the horizontal layout
        main_layout.addWidget(self.request_widget, 25)  # 50% width


    def _setup_response_section(self, main_layout):
        self.empty_widget_2 = ResponseWidget()
        main_layout.addWidget(self.empty_widget_2, 50)  # 25% width
