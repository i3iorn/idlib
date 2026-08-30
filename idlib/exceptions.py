from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # Deferred to avoid a circular import: idlib.snowflake (needed by
    # idlib.utils for IdType.SNOWFLAKE) raises ClockMovedBackwardsException
    # from this module, so this module cannot import idlib.utils at runtime.
    from idlib.utils import IdType


class InvalidIDLengthException(Exception):
    """Exception raised when the ID length is invalid."""

    def __init__(self, length: int, min_length: int, max_length: int):
        super().__init__(f"Invalid ID length: {length}. Expected between {min_length} and {max_length}.")
        self.length = length
        self.min_length = min_length
        self.max_length = max_length


class InvalidIDTypeException(Exception):
    """Exception raised when the ID type is invalid."""

    def __init__(self, expected_type: "IdType", actual_type: Any):
        super().__init__(f"Invalid ID type: {actual_type}. Expected {expected_type}.")
        self.expected_type = expected_type
        self.actual_type = actual_type


class IdAlreadySetException(Exception):
    """Exception raised when trying to change an Id's value after it has already been set."""

    def __init__(self):
        super().__init__("Id value has already been set and cannot be reassigned.")


class ClockMovedBackwardsException(Exception):
    """Exception raised when the system clock moves backwards during Snowflake id generation."""

    def __init__(self, last_timestamp: int, current_timestamp: int):
        super().__init__(
            f"Clock moved backwards: last timestamp {last_timestamp}, current timestamp {current_timestamp}."
        )
        self.last_timestamp = last_timestamp
        self.current_timestamp = current_timestamp
