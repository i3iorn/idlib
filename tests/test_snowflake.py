import threading

import pytest

from idlib.exceptions import ClockMovedBackwardsException
from idlib.snowflake import SnowflakeGenerator, default_machine_id


def test_default_machine_id_fits_in_10_bits():
    assert 0 <= default_machine_id() <= 1023


def test_machine_id_out_of_range_is_rejected():
    with pytest.raises(ValueError):
        SnowflakeGenerator(machine_id=1024)
    with pytest.raises(ValueError):
        SnowflakeGenerator(machine_id=-1)


def test_next_id_returns_increasing_values_for_sequential_calls():
    generator = SnowflakeGenerator()
    values = [generator.next_id() for _ in range(50)]
    assert values == sorted(values)
    assert len(set(values)) == len(values)


def test_ids_are_unique_across_threads():
    generator = SnowflakeGenerator()
    results = []
    lock = threading.Lock()

    def worker():
        local = [generator.next_id() for _ in range(500)]
        with lock:
            results.extend(local)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 4000
    assert len(set(results)) == len(results)


def test_different_machine_ids_do_not_collide_at_same_moment():
    a = SnowflakeGenerator(machine_id=1)
    b = SnowflakeGenerator(machine_id=2)
    assert a.next_id() != b.next_id()


def test_clock_moved_backwards_raises():
    generator = SnowflakeGenerator()
    generator._last_timestamp = generator._current_timestamp() + 10_000
    with pytest.raises(ClockMovedBackwardsException):
        generator.next_id()
