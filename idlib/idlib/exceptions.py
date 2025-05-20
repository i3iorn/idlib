from typing import Any

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

    def __init__(self, expected_type: IdType, actual_type: Any):
        super().__init__(f"Invalid ID type: {actual_type}. Expected {expected_type}.")
        self.expected_type = expected_type
        self.actual_type = actual_type