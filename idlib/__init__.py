from idlib.descriptor import IdDescriptor
from idlib.utils import IdType


class Id:
    """
    A class representing an ID.

    This class is used to generate and manage unique identifiers.
    """
    _id = IdDescriptor()

    def __init__(self, id_type: IdType = IdType.UUID, id_length: int = 16):
        """
        Initialize the Id class.

        Arguments:
        ----------
        id_type : IdType
            The type of ID to generate (UUID, HEX, BASE64).
        id_length : int
            The length of the ID to generate (not applicable for UUID).
        """
        self._id_type = id_type
        self._id_length = id_length

    @property
    def id(self):
        """The underlying id value, generated lazily on first access."""
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        return f"{type(self).__name__}({self.id!r})"

    def __eq__(self, other):
        if not isinstance(other, Id):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)
