from PyQt6.QtCore import pyqtSignal, QObject

from api_viewer.worker_result import WorkerResult


class SignalEmitter(QObject):
    """
    Emitter of application-wide signals.  Just a plain QObject subclass.
    """

    statusBarMessage      = pyqtSignal(str, int)
    error                 = pyqtSignal(str, str, str)
    themeChanged          = pyqtSignal(str, str)
    log                   = pyqtSignal(str, str)
    apiAvailable          = pyqtSignal(str)
    requestBodyChanged    = pyqtSignal(str)
    reloadSpecifications  = pyqtSignal()
    uiLoaded              = pyqtSignal()
    dynamicControlUpdated = pyqtSignal()
    loadRequestId         = pyqtSignal(int)
    reloadBodyFromHistory = pyqtSignal(int)

    jobStarted            = pyqtSignal(str)
    jobFinished           = pyqtSignal(str)
    jobResult             = pyqtSignal(str, WorkerResult)
    jobProgress           = pyqtSignal(str, int)
    jobError              = pyqtSignal(str, tuple)


# the one and only global instance:
signal_emitter = SignalEmitter()
