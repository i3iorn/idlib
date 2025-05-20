from dataclasses import dataclass
from typing import Any


@dataclass
class WorkerResult:
    """
    A simple class to hold the
    result of a worker thread.
    """
    result: Any
