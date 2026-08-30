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