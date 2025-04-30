import logging
import sys
from threading import Lock

from PyQt6.QtWidgets import QApplication

from constants import STARTUP_WINDOW_TITLE
from log import setup_logging
from emitter import SignalEmitter
from window import MainWindow
from api import *

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