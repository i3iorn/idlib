import logging


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
