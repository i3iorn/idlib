from idlib.generator import IdGenerator


class IdDescriptor:
    """
    Descriptor that lazily generates and caches an ID on first access.
    """
    def __set_name__(self, owner, name):
        self._name = f"_{name}_value"

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self._get_id(instance)

    def __set__(self, instance, value):
        self._set_id(instance, value)

    def _get_id(self, instance):
        if getattr(instance, self._name, None) is None:
            value = IdGenerator.generate_id(instance._id_type, instance._id_length)
            setattr(instance, self._name, value)
        return getattr(instance, self._name)

    def _set_id(self, instance, value):
        setattr(instance, self._name, value)
