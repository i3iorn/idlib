import functools
import random
import string
import uuid
from enum import Enum


def _generate_int(n: int) -> int:
    """Return an int with exactly n significant digits (no leading zero)."""
    if n <= 1:
        return int(random.choice(string.digits))
    first_digit = random.choice("123456789")
    rest = "".join(random.choices(string.digits, k=n - 1))
    return int(first_digit + rest)


class IdType(Enum):
    """
    Enum to represent the ID types.

    Each member's value is a callable (wrapped in functools.partial so Enum
    treats it as a value rather than a method) that generates the id. UUID
    takes no arguments; the others take the desired length ``n``.
    """
    UUID = functools.partial(uuid.uuid4)
    STR = functools.partial(lambda n: "".join(random.choices(string.ascii_letters, k=n)))
    INT = functools.partial(_generate_int)
    HEX = functools.partial(lambda n: "".join(random.choices("0123456789abcdef", k=n)))
    BASE64 = functools.partial(lambda n: "".join(random.choices(string.ascii_letters + string.digits + "+/", k=n)))
    #: Opaque ASCII-derived bytes (letters/digits encoded as utf-8), not raw
    #: random bytes; not suitable where full byte-value entropy is required.
    BYTES = functools.partial(lambda n: "".join(random.choices(string.ascii_letters + string.digits, k=n)).encode("utf-8"))
