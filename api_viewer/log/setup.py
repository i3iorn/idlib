import logging
from logging.handlers import RotatingFileHandler

from api_viewer.log.formatters import ExpandedFormatter
from api_viewer.log.handlers import SignalHandler


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
