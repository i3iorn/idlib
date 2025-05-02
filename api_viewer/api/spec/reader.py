import logging

from api_viewer.api.protocol import Protocol
from api_viewer.api.spec.address import SpecAddress
from api_viewer.log.decorator import log_method_calls

logger = logging.getLogger(__name__)


@log_method_calls()
class SpecReader:
    """
    Read a spec from a given address.
    This class is used to read a spec from a given address.
    It uses the Protocol class to determine the protocol and handler to use.
    The address should be in the format of <protocol>://<address>.

    Attributes:
        _address (SpecAddress): The address of the spec.
        _protocol (Protocol): The protocol of the spec.
        _handler (BaseHandler): The handler for the spec.

    Methods:
        __init__(spec_address: str) -> None:
            Initializes the SpecReader with the given address.

        read() -> str:
            Reads the spec from the given address.
    """
    def __init__(self, spec_address: str) -> None:
        """
        Initializes the SpecReader with the given address.
        Args:
            spec_address (str): The address of the spec.
        Raises:
            ValueError: If the address is not valid.
        Returns:
            None
        Examples:
            >>> reader = SpecReader("http://example.com/spec")
            >>> spec = reader.read()
        """
        self._address = SpecAddress(spec_address)

        try:
            self._protocol = Protocol.from_spec_address(self._address)
        except ValueError as e:
            logger.error(f"Invalid spec address: {spec_address}")
            raise ValueError(
                f"Invalid spec address: {spec_address}"
            ) from e

        self._handler = self._protocol.handler_class(
            str(self._address),
            self._protocol.function,
            self._protocol.params,
            self._protocol.read_method
        )

    def exists(self) -> bool:
        """
        Checks if the spec exists at the given address.
        Args:
            None
        Returns:
            bool: True if the spec exists, False otherwise.
        Raises:
            ValueError: If the address is not valid.
            AttributeError: If the handler does not have an exists method.
        Examples:
            >>> reader = SpecReader("http://example.com/spec")
            >>> exists = reader.exists()
            >>> print(exists)
        """
        try:
            return self._handler.exists()
        except AttributeError:
            logger.warning(
                f"Handler for {self._address} does not support 'exists' method"
            )
            return False

    def read(self) -> str:
        """
        Reads the spec from the given address.
        Args:
            None
        Returns:
            str: The spec as a string.
        Raises:
            ValueError: If the address is not valid.
            AttributeError: If the handler does not have a read method.
        Examples:
            >>> reader = SpecReader("http://example.com/spec")
            >>> spec = reader.read()
            >>> print(spec)
        """
        try:
            return self._handler.read()
        except AttributeError:
            logger.error(
                f"Handler for {self._address} does not support 'read' method"
            )
            raise NotImplementedError(
                f"Handler for {self._address} does not support 'read' method"
            )
