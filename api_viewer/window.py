import logging
import sys

from PyQt6.QtCore import QRunnable
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QApplication

from api_viewer.emitter import signal_emitter
from api_viewer.central_widget import CentralWidget
from constants import STARTUP_WINDOW_X, STARTUP_WINDOW_Y, STARTUP_WINDOW_WIDTH, STARTUP_WINDOW_HEIGHT

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, signal_emitter, parent=None):
        super().__init__(parent)
        self.signal_emitter = signal_emitter
        self.setWindowTitle("API Viewer")
        height = min(STARTUP_WINDOW_HEIGHT, QApplication.primaryScreen().size().height() - 2*STARTUP_WINDOW_Y)
        width = min(STARTUP_WINDOW_WIDTH, QApplication.primaryScreen().size().width() - 2*STARTUP_WINDOW_X)

        self.setGeometry(STARTUP_WINDOW_X, STARTUP_WINDOW_Y, width, height)
        self.setMinimumSize(width, height)

        sys.excepthook = self.custom_sys_exception_hook
        self._setup_ui()

    def _setup_ui(self):
        self._setup_menu()
        self._setup_central_widget()
        self._setup_status_bar()
        self._connect_signals()

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
        load_action.triggered.connect(signal_emitter.reloadSpecifications.emit)

    def _setup_central_widget(self):
        central_widget = CentralWidget(self)
        self.setCentralWidget(central_widget)

    def _setup_status_bar(self):
        # Create a status bar
        status_bar = self.statusBar()
        status_bar.showMessage("Ready")

    def _connect_signals(self):
        # Connect signals to methods
        signal_emitter.jobError.connect(self._handle_job_error)

    def _handle_job_error(self, job_id: str, exception_info: tuple):
        """
        Handle job errors by displaying a message box.
        """
        logger.error(f"Job error: {job_id}")
        exception, tb = exception_info
        logger.error(f"Exception: {exception}")
        logger.error(f"Traceback: {tb}")
        msg_box = QMessageBox(
            QMessageBox.Icon.Critical,
            "Job Error",
            f"An error occurred in job {job_id}:\n{exception}",
            QMessageBox.StandardButton.Ok,
            self
        )
        msg_box.exec()

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
