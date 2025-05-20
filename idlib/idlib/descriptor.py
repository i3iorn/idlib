class IdDescriptor:
    """
    Class to represent an ID descriptor.
    """
    def __get__(self, instance, owner):
        """
        Get the ID for an instance.
        :param instance: The instance of the class.
        :param owner: The owner class.
        :return: The ID.
        """
        if instance is None:
            return self
        return self._get_id(instance)

    def __set__(self, instance, value):
        """
        Set the ID for an instance.
        :param instance: The instance of the class.
        :param value: The value to set.
        """
        self._set_id(instance, value)

    def _get_id(self, instance):
        """
        Get the ID for an instance.
        :param instance:
        :return:
        """
        raise NotImplementedError("Subclasses must implement this method.")