import logging
from logging.handlers import RotatingFileHandler


class ExpandedFormatter(logging.Formatter):
    """
    A custom formatter that appends extra fields with the prefix 'extra_'.
    """

    def __init__(self, fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                 datefmt="%Y-%m-%d, %H:%M:%S", style='%', validate=True):
        super().__init__(fmt=fmt, datefmt=datefmt, style=style, validate=validate)

    def format(self, record):
        # First, get the base log message from the parent class
        base = super().format(record)

        # Prepare the 'extra' dictionary that will hold extra fields
        extra = {}

        # Include fields passed in 'record.args' (these might include extra fields)
        for argument in record.args:
            if isinstance(argument, dict):
                for key, value in argument.items():
                    extra[key] = value

        # If any fields are in 'extra' (added with prefix 'extra_'), include them in the log message
        for key, value in record.__dict__.items():
            if key.startswith("extra_"):
                new_key = key[6:]  # Strip the 'extra_' prefix
                extra[new_key] = value

        # If extra data exists, append it to the base log message
        if extra:
            base = f"{base} | additional={extra!r}"

        return base


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
            logging.error(f"Error emitting signal: {e}")


def setup_logging(signal_emitter=None, level=logging.DEBUG) -> None:
    """
    Sets up logging with a custom logger, formatter, and handlers.
    Optionally takes a signal emitter and log file path.
    """

    # Create and configure the root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Add the custom signal handler to the root logger
    if signal_emitter:
        signal_handler = SignalHandler(signal_emitter)
        signal_handler.setFormatter(ExpandedFormatter())  # Apply custom formatter
        logger.addHandler(signal_handler)

    # Console handler with custom formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ExpandedFormatter())
    logger.addHandler(console_handler)

    # File handler with rotation
    file_handler = RotatingFileHandler("app.log", maxBytes=10 ** 6, backupCount=3)
    file_handler.setFormatter(ExpandedFormatter())
    logger.addHandler(file_handler)

    # Log a message to confirm setup
    logger.debug("Logging setup complete.")
