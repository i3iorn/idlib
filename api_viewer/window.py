from PyQt6.QtWidgets import QMainWindow, QVBoxLayout

from src.central_widget import CentralWidget
from constants import *


class MainWindow(QMainWindow):
    def __init__(self, signal_emitter, parent=None):
        super().__init__(parent)
        self.signal_emitter = signal_emitter
        self.setWindowTitle("API Viewer")
        self.setGeometry(STARTUP_WINDOW_X, STARTUP_WINDOW_Y, STARTUP_WINDOW_WIDTH, STARTUP_WINDOW_HEIGHT)
        self.setMinimumSize(STARTUP_WINDOW_WIDTH, STARTUP_WINDOW_HEIGHT)

        self._setup_ui()
        self._load_api_data()

    def _setup_ui(self):
        self._setup_menu()
        self._setup_central_widget()
        self._setup_status_bar()

    def _load_api_data(self):
        # Load API data here
        # For example, you can load the API data from a file or an API endpoint
        # and then update the central widget with the loaded data.
        pass

    def _setup_menu(self):
        # Create a menu bar
        menu_bar = self.menuBar()

        # Create a file menu
        file_menu = menu_bar.addMenu("File")

        # Create actions for the file menu
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

    def _setup_central_widget(self):
        central_widget = CentralWidget(self)
        self.setCentralWidget(central_widget)

    def _setup_status_bar(self):
        # Create a status bar
        status_bar = self.statusBar()
        status_bar.showMessage("Ready")
