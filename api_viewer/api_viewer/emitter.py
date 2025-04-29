from PyQt6.QtCore import pyqtSignal, QObject


class SignalEmitter(QObject):
    """
    A class that emits signals for various events.
    """

    # Signal for updating the status bar message (message, timeout)
    status_bar_message  = pyqtSignal(str, int)

    # Signal for when an error occurs ( exeption class, error message , json formatted extra data)
    error               = pyqtSignal(str, str, str)

    # Signal for when a request is made (request method, request url, request body, request headers)
    request             = pyqtSignal(str, str, str, str)

    # Signal for when a response is received (response status code, response body, response headers)
    response            = pyqtSignal(int, str, str)

    # Signal for theme change (theme name, full stylesheet)
    theme_changed       = pyqtSignal(str, str)

    # Log signal (log level, log message)
    log                 = pyqtSignal(str, str)

    # Signal for when an api is made available ( api name )
    api_available       = pyqtSignal(str)
