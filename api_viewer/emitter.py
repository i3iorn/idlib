from PyQt6.QtCore import pyqtSignal, QObject

from api_viewer.worker_result import WorkerResult


class SignalEmitter(QObject):
    """
    Emitter of application-wide signals.  Just a plain QObject subclass.
    """

    status_bar_message    = pyqtSignal(str, int)
    error                 = pyqtSignal(str, str, str)
    request               = pyqtSignal(str)
    response              = pyqtSignal(str)
    theme_changed         = pyqtSignal(str, str)
    log                   = pyqtSignal(str, str)
    api_available         = pyqtSignal(str)
    request_body_changed  = pyqtSignal(str)
    reload_specifications = pyqtSignal()
    ui_loaded             = pyqtSignal()

    job_started           = pyqtSignal(str)
    job_finished          = pyqtSignal(str)
    job_result            = pyqtSignal(str, WorkerResult)
    job_progress          = pyqtSignal(str, int)
    job_error             = pyqtSignal(str, tuple)


# the one and only global instance:
signal_emitter = SignalEmitter()
