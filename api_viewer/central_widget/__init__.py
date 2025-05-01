from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QSlider, QSplitter

from api_viewer.constants import NO_MARGIN
from api_viewer.central_widget.config_widget import ConfigWidget
from api_viewer.central_widget.request_widget import RequestWidget
from api_viewer.central_widget.response_widget import ResponseWidget


class CentralWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        # Set up the main layout (Vertical)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(*NO_MARGIN)
        splitter_widget = QSplitter(Qt.Orientation.Horizontal, self)
        splitter_widget.setContentsMargins(*NO_MARGIN)
        splitter_widget.setHandleWidth(5)
        splitter_widget.setChildrenCollapsible(True)
        splitter_widget.setStretchFactor(1,1)
        splitter_widget.setStretchFactor(2,1)
        splitter_widget.setStretchFactor(3,1)
        main_layout.addWidget(splitter_widget)

        self._setup_conf_section(splitter_widget)
        self._setup_request_section(splitter_widget)
        self._setup_response_section(splitter_widget)

        self.setLayout(main_layout)

    def _setup_conf_section(self, main_layout):
        # Create the combo boxes and add them to the layout
        conf_widget = ConfigWidget(self)
        main_layout.addWidget(conf_widget)

    def _setup_request_section(self, main_layout):
        # Create two empty widgets
        self.request_widget = RequestWidget(self)
        # Add the empty widgets to the horizontal layout
        main_layout.addWidget(self.request_widget)


    def _setup_response_section(self, main_layout):
        self.empty_widget_2 = ResponseWidget()
        main_layout.addWidget(self.empty_widget_2)
