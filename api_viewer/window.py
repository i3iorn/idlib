import logging
import sys

from PyQt6.QtWidgets import QMainWindow, QMessageBox

from api_viewer.api import load_apis, load_clients
from api_viewer.central_widget import CentralWidget
from constants import STARTUP_WINDOW_X, STARTUP_WINDOW_Y, STARTUP_WINDOW_WIDTH, STARTUP_WINDOW_HEIGHT

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, signal_emitter, parent=None):
        super().__init__(parent)
        self.signal_emitter = signal_emitter
        self.setWindowTitle("API Viewer")
        self.setGeometry(STARTUP_WINDOW_X, STARTUP_WINDOW_Y, STARTUP_WINDOW_WIDTH, STARTUP_WINDOW_HEIGHT)
        self.setMinimumSize(STARTUP_WINDOW_WIDTH, STARTUP_WINDOW_HEIGHT)

        self._load_api_data()
        self._setup_ui()
        sys.excepthook = self.custom_sys_exception_hook

    def _setup_ui(self):
        self._setup_menu()
        self._setup_central_widget()
        self._setup_status_bar()

    def _load_api_data(self):
        load_clients()
        load_apis()

    def _setup_menu(self):
        # Create a menu bar
        menu_bar = self.menuBar()

        # Create a file menu
        file_menu = menu_bar.addMenu("File")

        # Create actions for the file menu
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        # Create specification menu
        spec_menu = menu_bar.addMenu("Specification")

        # Create actions for the specification menu
        load_action = spec_menu.addAction("Reload Specifications")
        load_action.triggered.connect(self._load_api_data)

    def _setup_central_widget(self):
        central_widget = CentralWidget(self)
        self.setCentralWidget(central_widget)

    def _setup_status_bar(self):
        # Create a status bar
        status_bar = self.statusBar()
        status_bar.showMessage("Ready")

    def custom_sys_exception_hook(self, type, value, traceback):
        """
        Custom exception hook to handle uncaught exceptions.
        """
        # Log the exception or show a message box
        logger.debug(f"Uncaught exception: {value}", exc_info=(type, value, traceback))
        msg_box = QMessageBox(
            QMessageBox.Icon.Critical,
            "Uncaught Exception",
            f"An uncaught exception occurred:\n{value}",
            QMessageBox.StandardButton.Ok,
            self
        )
        msg_box.exec()
