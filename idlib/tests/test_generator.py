import uuid

import pytest

from idlib import exceptions
from idlib.constants import MAX_ID_LENGTH, MIN_ID_LENGTH
from idlib.generator import IdGenerator
from idlib.utils import IdType


def test_generate_uuid_ignores_length():
    value = IdGenerator.generate_id(IdType.UUID)
    assert isinstance(value, uuid.UUID)


@pytest.mark.parametrize("id_type", [IdType.STR, IdType.HEX, IdType.BASE64])
def test_generate_string_types_respect_length(id_type):
    value = IdGenerator.generate_id(id_type, MIN_ID_LENGTH)
    assert isinstance(value, str)
    assert len(value) == MIN_ID_LENGTH


def test_generate_bytes_type():
    value = IdGenerator.generate_id(IdType.BYTES, MIN_ID_LENGTH)
    assert isinstance(value, bytes)
    assert len(value) == MIN_ID_LENGTH


def test_generate_int_type():
    value = IdGenerator.generate_id(IdType.INT, MIN_ID_LENGTH)
    assert isinstance(value, int)


@pytest.mark.parametrize("length", [MIN_ID_LENGTH - 1, MAX_ID_LENGTH + 1])
def test_generate_rejects_out_of_range_length(length):
    with pytest.raises(exceptions.InvalidIDLengthException):
        IdGenerator.generate_id(IdType.STR, length)


def test_generate_rejects_non_int_length():
    with pytest.raises(exceptions.InvalidIDLengthException):
        IdGenerator.generate_id(IdType.STR, "20")


def test_generate_rejects_invalid_type():
    with pytest.raises(exceptions.InvalidIDTypeException):
        IdGenerator.generate_id("not-a-type", MIN_ID_LENGTH)
