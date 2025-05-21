class IdDescriptor:
    """
    Class to represent an ID descriptor.
    """
    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self._get_id(instance)

    def __set__(self, instance, value):
        self._set_id(instance, value)

    def _get_id(self, instance):
