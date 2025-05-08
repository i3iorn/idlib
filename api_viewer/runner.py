from typing import Any, Callable
import traceback

from PyQt6.QtCore import QRunnable

from api_viewer.emitter import signal_emitter  # your singleton emitter
from api_viewer.worker_result import WorkerResult


class WorkerThread(QRunnable):
    """
    QRunnable wrapper that runs a function in a background thread
    and emits through the global `signal_emitter` on start, success,
    failure, and completion.
    """

    def __init__(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self.func   = func
        self.args   = args
        self.kwargs = kwargs
        self._job_id = self._generate_id()

    def _generate_id(self) -> str:
        """
        Generate a unique job ID. This can be replaced with a more
        sophisticated ID generation method if needed.
        """
        return f"job-{id(self)}"

    @property
    def job_id(self) -> str:
        """
        Return the job ID.
        """
        return self._job_id

    def run(self) -> None:
        """
        Execute the target function with the provided arguments,
        emitting the appropriate signals via `signal_emitter`.
        """
        # signal_emitter must have these pyqtSignal attributes:
        #   started, result, error, finished
        signal_emitter.jobStarted.emit(self.job_id)

        try:
            result = self.func(*self.args, **self.kwargs)
        except Exception as e:
            tb = traceback.format_exc()
            # emit a tuple (exception instance, traceback string)
            signal_emitter.jobError.emit(self.job_id, (e, tb))
        else:
            signal_emitter.jobResult.emit(self.job_id, WorkerResult(result))
        finally:
            signal_emitter.jobFinished.emit(self.job_id)
