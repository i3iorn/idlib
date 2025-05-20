import logging


class SignalHandler(logging.Handler):
    """
    A custom logging handler that emits logs via a signal emitter.
    """

    def __init__(self, signal_emitter):
        super().__init__()
        self.signal_emitter = signal_emitter

    def emit(self, record):
        try:
            msg = self.format(record)
        except Exception as e:
            msg = f"Error formatting log message: {e}"
            logging.error(msg)
            # Fallback in case of failure
            msg = record.getMessage()
        # Emit the log message via the signal emitter
        if not self.signal_emitter:
            logging.error("Signal emitter is not set.")
            return
        try:
            self.signal_emitter.log.emit(record.levelname, msg)
        except Exception as e:
            # Fallback in case of failure
            print(f"Error emitting log message: {e}", self.signal_emitter, self.signal_emitter.log, record.levelname, msg)
