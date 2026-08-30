from idlib import Id
from idlib.utils import IdType


def test_default_id_is_uuid_like():
    value = Id()._id
    assert isinstance(value, object)
    assert str(value).count("-") == 4


def test_id_is_generated_lazily_and_cached():
    instance = Id(IdType.HEX, id_length=20)
    first = instance._id
    second = instance._id
    assert first == second


def test_id_can_be_overwritten():
    instance = Id(IdType.HEX, id_length=20)
    instance._id = "custom-id"
    assert instance._id == "custom-id"


def test_two_instances_get_independent_ids():
    a = Id(IdType.STR, id_length=20)
    b = Id(IdType.STR, id_length=20)
    assert a._id != b._id
