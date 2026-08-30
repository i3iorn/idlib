import pytest

from idlib.descriptor import IdDescriptor
from idlib.exceptions import IdAlreadySetException
from idlib.utils import IdType


class _Owner:
    value = IdDescriptor()

    def __init__(self, id_type=IdType.HEX, id_length=20):
        self._id_type = id_type
        self._id_length = id_length


def test_descriptor_accessed_on_class_returns_itself():
    assert isinstance(_Owner.value, IdDescriptor)


def test_descriptor_generates_on_first_access():
    instance = _Owner()
    value = instance.value
    assert isinstance(value, str)
    assert len(value) == 20


def test_descriptor_set_before_access_is_used_verbatim():
    instance = _Owner()
    instance.value = "explicit-value"
    assert instance.value == "explicit-value"


def test_descriptor_rejects_reassignment_after_set():
    instance = _Owner()
    instance.value = "explicit-value"
    with pytest.raises(IdAlreadySetException):
        instance.value = "other-value"


def test_descriptor_rejects_reassignment_after_generation():
    instance = _Owner()
    instance.value  # noqa: B018 - trigger generation
    with pytest.raises(IdAlreadySetException):
        instance.value = "explicit-value"


def test_two_instances_share_no_state():
    a = _Owner()
    b = _Owner()
    a.value = "a-value"
    assert b.value != "a-value"
