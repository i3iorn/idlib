import logging
import sys
from threading import Lock

from PyQt6.QtWidgets import QApplication

from api_viewer.constants import STARTUP_WINDOW_TITLE
from api_viewer.log import setup_logging
from api_viewer.emitter import SignalEmitter
from api_viewer.window import MainWindow
from api_viewer.api import *

class APIRegistry:
    _instance = None
    _registry = {}
    _lock = Lock()

signal_emitter = SignalEmitter()
setup_logging(signal_emitter)

application = QApplication(
    sys.argv
)
application.setApplicationName(STARTUP_WINDOW_TITLE)

application.setStyle("Fusion")
window = MainWindow(signal_emitter)
window.show()
sys.exit(application.exec())