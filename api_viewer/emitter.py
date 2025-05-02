from PyQt6.QtCore import pyqtSignal, QObject


class SignalEmitter(QObject):
    """
    A class that emits signals for various events.
    """

    # Signal for updating the status bar message (message, timeout)
    status_bar_message  = pyqtSignal(str, int)

    # Signal for when an error occurs ( exeption class, error message , json formatted extra data)
    error               = pyqtSignal(str, str, str)

    # Signal for when a request is made (http formatted request)
    request             = pyqtSignal(str)

    # Signal for when a response is received (http formatted response)
    response            = pyqtSignal(str)

    # Signal for theme change (theme name, full stylesheet)
    theme_changed       = pyqtSignal(str, str)

    # Log signal (log level, log message)
    log                 = pyqtSignal(str, str)

    # Signal for when an api is made available ( api name )
    api_available       = pyqtSignal(str)

    # Signal for when the request body is changed (valid json or not)
    request_body_changed = pyqtSignal(str)

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SignalEmitter, cls).__new__(cls)
            cls._initialize = False
        return cls._instance

    def __init__(self):
        if not self._initialize:
            super().__init__()
            self._initialize = True