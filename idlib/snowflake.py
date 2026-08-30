from __future__ import annotations

import hashlib
import os
import socket
import threading
import time

from idlib.exceptions import ClockMovedBackwardsException

#: Custom epoch (2024-01-01T00:00:00Z in ms) so the 41-bit timestamp field
#: doesn't waste range on the decades before this library existed.
EPOCH_MS = 1704067200000

TIMESTAMP_BITS = 41
MACHINE_ID_BITS = 10
SEQUENCE_BITS = 12

_MAX_SEQUENCE = (1 << SEQUENCE_BITS) - 1
_MAX_MACHINE_ID = (1 << MACHINE_ID_BITS) - 1
_MACHINE_ID_SHIFT = SEQUENCE_BITS
_TIMESTAMP_SHIFT = SEQUENCE_BITS + MACHINE_ID_BITS


def default_machine_id() -> int:
    """
    Derive a machine_id-bit id from this host and process.

    Not a strict uniqueness guarantee across an entire fleet (the id space
    is only 1024 values), but combined with the timestamp and sequence it
    makes accidental collisions between concurrently-running processes
    overwhelmingly unlikely without requiring any shared coordination.
    """
    raw = f"{socket.gethostname()}:{os.getpid()}".encode()
    digest = hashlib.sha256(raw).digest()
    return int.from_bytes(digest[:2], "big") & _MAX_MACHINE_ID


class SnowflakeGenerator:
    """
    Thread-safe generator of unique 63-bit ids, composed of a millisecond
    timestamp, a machine/process id, and a per-millisecond sequence number
    (the classic Twitter Snowflake layout: 41 + 10 + 12 bits).

    Ids are unique across threads within one process by construction (the
    sequence counter is protected by a lock), and unique across processes
    and hosts as long as no two processes share the same
    (machine_id, timestamp, sequence) triple -- overwhelmingly likely given
    the machine id is derived from the hostname and process id.
    """

    def __init__(self, machine_id: int | None = None):
        if machine_id is None:
            machine_id = default_machine_id()
        if not (0 <= machine_id <= _MAX_MACHINE_ID):
            raise ValueError(f"machine_id must be between 0 and {_MAX_MACHINE_ID}, got {machine_id}")

        self._machine_id = machine_id
        self._lock = threading.Lock()
        self._last_timestamp = -1
        self._sequence = 0

    @staticmethod
    def _current_timestamp() -> int:
        return int(time.time() * 1000) - EPOCH_MS

    def next_id(self) -> int:
        """Return the next unique id. Thread-safe."""
        with self._lock:
            timestamp = self._current_timestamp()

            if timestamp < self._last_timestamp:
                raise ClockMovedBackwardsException(self._last_timestamp, timestamp)

            if timestamp == self._last_timestamp:
                self._sequence = (self._sequence + 1) & _MAX_SEQUENCE
                if self._sequence == 0:
                    # Sequence exhausted for this millisecond: wait for the next one.
                    while timestamp <= self._last_timestamp:
                        timestamp = self._current_timestamp()
            else:
                self._sequence = 0

            self._last_timestamp = timestamp
            return (timestamp << _TIMESTAMP_SHIFT) | (self._machine_id << _MACHINE_ID_SHIFT) | self._sequence


default_snowflake_generator = SnowflakeGenerator()
