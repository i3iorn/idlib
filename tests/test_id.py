import pytest

from idlib import Id
from idlib.exceptions import IdAlreadySetException
from idlib.utils import IdType


def test_default_id_is_uuid_like():
    value = Id().id
    assert str(value).count("-") == 4


def test_id_is_generated_lazily_and_cached():
    instance = Id(IdType.HEX, id_length=20)
    first = instance.id
    second = instance.id
    assert first == second


def test_id_can_be_set_before_first_access():
    instance = Id(IdType.HEX, id_length=20)
    instance.id = "custom-id"
    assert instance.id == "custom-id"


def test_id_cannot_be_reassigned_after_being_set():
    instance = Id(IdType.HEX, id_length=20)
    instance.id = "custom-id"
    with pytest.raises(IdAlreadySetException):
        instance.id = "another-id"
    assert instance.id == "custom-id"


def test_id_cannot_be_reassigned_after_being_generated():
    instance = Id(IdType.HEX, id_length=20)
    generated = instance.id
    with pytest.raises(IdAlreadySetException):
        instance.id = "custom-id"
    assert instance.id == generated


def test_two_instances_get_independent_ids():
    a = Id(IdType.STR, id_length=20)
    b = Id(IdType.STR, id_length=20)
    assert a.id != b.id


def test_str_and_repr_reflect_id_value():
    instance = Id(IdType.HEX, id_length=20)
    instance.id = "custom-id"
    assert str(instance) == "custom-id"
    assert repr(instance) == "Id('custom-id')"


def test_equality_and_hash_are_based_on_id_value():
    a = Id(IdType.HEX, id_length=20)
    a.id = "same-id"
    b = Id(IdType.HEX, id_length=20)
    b.id = "same-id"
    c = Id(IdType.HEX, id_length=20)
    c.id = "different-id"

    assert a == b
    assert hash(a) == hash(b)
    assert a != c
    assert a != "same-id"
