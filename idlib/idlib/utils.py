import functools
import random
import string
import uuid
from enum import Enum


class IdType(Enum):
    """
    Enum to represent the ID types.

    Each member's value is a callable (wrapped in functools.partial so Enum
    treats it as a value rather than a method) that generates the id. UUID
    takes no arguments; the others take the desired length ``n``.
    """
    UUID = functools.partial(uuid.uuid4)
    STR = functools.partial(lambda n: "".join(random.choices(string.ascii_letters, k=n)))
    INT = functools.partial(lambda n: int("".join(random.choices(string.digits, k=n))))
    HEX = functools.partial(lambda n: "".join(random.choices(string.hexdigits, k=n)))
    BASE64 = functools.partial(lambda n: "".join(random.choices(string.ascii_letters + string.digits + "+/", k=n)))
    BYTES = functools.partial(lambda n: "".join(random.choices(string.ascii_letters + string.digits, k=n)).encode("utf-8"))
