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


def test_generate_hex_is_lowercase():
    value = IdGenerator.generate_id(IdType.HEX, MIN_ID_LENGTH)
    assert value == value.lower()
    assert all(c in "0123456789abcdef" for c in value)


def test_generate_bytes_type():
    value = IdGenerator.generate_id(IdType.BYTES, MIN_ID_LENGTH)
    assert isinstance(value, bytes)
    assert len(value) == MIN_ID_LENGTH


def test_generate_int_type():
    value = IdGenerator.generate_id(IdType.INT, MIN_ID_LENGTH)
    assert isinstance(value, int)
    assert len(str(value)) == MIN_ID_LENGTH


def test_generate_int_type_never_has_leading_zero():
    for _ in range(200):
        value = IdGenerator.generate_id(IdType.INT, MIN_ID_LENGTH)
        assert len(str(value)) == MIN_ID_LENGTH
        assert str(value)[0] != "0"


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


def test_invalid_id_length_exception_message():
    exc = exceptions.InvalidIDLengthException(5, MIN_ID_LENGTH, MAX_ID_LENGTH)
    assert str(exc) == f"Invalid ID length: 5. Expected between {MIN_ID_LENGTH} and {MAX_ID_LENGTH}."
    assert exc.length == 5
    assert exc.min_length == MIN_ID_LENGTH
    assert exc.max_length == MAX_ID_LENGTH


def test_invalid_id_type_exception_message():
    exc = exceptions.InvalidIDTypeException(IdType, "not-a-type")
    assert str(exc) == f"Invalid ID type: not-a-type. Expected {IdType}."
    assert exc.expected_type is IdType
    assert exc.actual_type == "not-a-type"


def test_id_already_set_exception_message():
    exc = exceptions.IdAlreadySetException()
    assert str(exc) == "Id value has already been set and cannot be reassigned."
