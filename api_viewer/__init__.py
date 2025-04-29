import logging
import sys
from threading import Lock

from PyQt6.QtWidgets import QApplication

from src.constants import STARTUP_WINDOW_TITLE
from src.log import setup_logging
from src.emitter import SignalEmitter
from src.window import MainWindow
from src.api import *

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