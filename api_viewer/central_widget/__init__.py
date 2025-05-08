import logging

from PyQt6.QtCore import Qt, QThreadPool
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QSlider, QSplitter, QTabWidget

from api_viewer.api import load_apis, load_clients
from api_viewer.central_widget.history_widget import HistoryWidget
from api_viewer.constants import NO_MARGIN
from api_viewer.central_widget.config_widget import ConfigWidget
from api_viewer.central_widget.request_widget import RequestWidget
from api_viewer.central_widget.response_widget import ResponseWidget
from api_viewer.emitter import signal_emitter
from api_viewer.log.decorator import log_method_calls
from api_viewer.runner import WorkerThread

logger = logging.getLogger(__name__)


@log_method_calls()
class CentralWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_data()
        signal_emitter.uiLoaded.emit()

    def _load_data(self):
        self.api_loader_thread = WorkerThread(
            func=load_apis
        )
        QThreadPool.globalInstance().start(self.api_loader_thread)
        self.client_loader_thread = WorkerThread(
            func=load_clients
        )
        QThreadPool.globalInstance().start(self.client_loader_thread)

    def _setup_ui(self):
        # Set up the main layout (Vertical)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(*NO_MARGIN)
        splitter_widget = QSplitter(Qt.Orientation.Horizontal, self)
        splitter_widget.setContentsMargins(*NO_MARGIN)
        splitter_widget.setHandleWidth(5)
        splitter_widget.setChildrenCollapsible(True)

        main_layout.addWidget(splitter_widget)

        self._setup_conf_section(splitter_widget)
        self._setup_request_section(splitter_widget)
        self._setup_response_section(splitter_widget)

        splitter_widget.setStretchFactor(0,2)
        splitter_widget.setStretchFactor(1,3)
        splitter_widget.setStretchFactor(2,4)

        self.setLayout(main_layout)

    def _setup_conf_section(self, main_layout):
        # Create the combo boxes and add them to the layout
        tab_group = QTabWidget(self)
        conf_widget = ConfigWidget(self)
        tab_group.addTab(conf_widget, "New Request")
        hist_widget = HistoryWidget(self)
        tab_group.addTab(hist_widget, "Historic Request")

        main_layout.addWidget(tab_group)

    def _setup_request_section(self, main_layout):
        # Create two empty widgets
        self.request_widget = RequestWidget(self)
        # Add the empty widgets to the horizontal layout
        main_layout.addWidget(self.request_widget)

    def _setup_response_section(self, main_layout):
        self.empty_widget_2 = ResponseWidget()
        main_layout.addWidget(self.empty_widget_2)

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.parent().close()
        else:
            super().keyPressEvent(a0)
