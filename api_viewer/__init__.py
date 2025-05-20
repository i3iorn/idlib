import asyncio
import sys
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

app = QApplication(sys.argv)
loop = QEventLoop(app)
asyncio.set_event_loop(loop)

def launch_window():
    from api_viewer.log.setup import setup_logging
    from api_viewer.emitter import signal_emitter
    from api_viewer.window import MainWindow

    setup_logging(signal_emitter)

    application = QApplication(
        sys.argv
    )

    from api_viewer.constants import STARTUP_WINDOW_TITLE
    application.setApplicationName(STARTUP_WINDOW_TITLE)

    application.setStyle("Fusion")
    main_window = MainWindow(signal_emitter)
    with loop:
        main_window.show()
        loop.run_forever()

    sys.exit(application.exec())


if __name__ == "__main__":
    launch_window()
