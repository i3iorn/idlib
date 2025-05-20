from idlib import exceptions
from idlib.constants import MAX_ID_LENGTH, MIN_ID_LENGTH
from idlib.utils import IdType


class IdGenerator:
    """
    Class to generate IDs of various types.
    """
    @staticmethod
    def generate_id(id_type: IdType, __n: int = 32) -> str:
        """
        Generate an ID of the specified type.

        Attributes:
        -----------
        id_type: IdType
            The type of ID to generate (UUID, STR, INT, FLOAT).
        __n: int
            The length of the ID to generate (for STR, INT, and FLOAT types).

        Returns:
        --------
        str
            The generated ID.

        Raises:
        -------
        InvalidIDLengthException
            If the length of the ID is not valid.

        InvalidIDTypeException
            If the ID type is not valid.
        """
        if id_type not in IdType:
            raise exceptions.InvalidIDTypeException(id_type, IdType)

        if id_type != IdType.UUID:
            if not isinstance(__n, int) or MAX_ID_LENGTH < __n < MIN_ID_LENGTH:
                raise exceptions.InvalidIDLengthException(__n, MIN_ID_LENGTH, MAX_ID_LENGTH)

        return id_type.value()
