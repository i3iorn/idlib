import sys

def launch_window():
    from PyQt6.QtWidgets import QApplication

    from api_viewer.log import setup_logging
    from api_viewer.emitter import SignalEmitter
    from api_viewer.window import MainWindow

    signal_emitter = SignalEmitter()
    setup_logging(signal_emitter)

    application = QApplication(
        sys.argv
    )

    from api_viewer.constants import STARTUP_WINDOW_TITLE
    application.setApplicationName(STARTUP_WINDOW_TITLE)

    application.setStyle("Fusion")
    window = MainWindow(signal_emitter)
    window.show()
    sys.exit(application.exec())


if __name__ == "__main__":
    launch_window()