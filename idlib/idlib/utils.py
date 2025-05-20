import random
import string
import uuid
from enum import Enum


class IdType(Enum):
    """
    Enum to represent the ID types.

    IdType.value() will be a tuple with the function to generate the id and input parameter validation callable
    """
    UUID = uuid.uuid4
    STR = lambda n: random.choices(string.ascii_letters, k=n)
    INT = lambda n: int("".join(random.choices(string.digits, k=n)))
    HEX = lambda n: "".join(random.choices(string.hexdigits, k=n))
    BASE64 = lambda n: "".join(random.choices(string.ascii_letters + string.digits + "+/", k=n))
    BYTES = lambda n: bytes(random.choices(string.ascii_letters + string.digits, k=n), 'utf-8')
