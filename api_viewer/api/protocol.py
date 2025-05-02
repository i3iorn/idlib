from abc import ABC, abstractmethod
from enum import Enum

import requests

from api_viewer.api.spec.address import SpecAddress
from api_viewer.log.decorator import log_method_calls


@log_method_calls()
class BaseProtocolHandler(ABC):
    """
    Base class for protocol handlers. This class is not meant to be used directly.
    Instead, use the Protocol enum to get the appropriate handler for a given protocol.
    Attributes:
        address (str): The address to connect to.
        function (callable): The function to call for the protocol.
        params (dict): The parameters to pass to the function.
        read_method (str): The method to call on the response object.

    This class is initialized with the address, function, parameters, and read method.
    The `read` method is an abstract method that must be implemented by subclasses.
    The `read` method is responsible for reading data from the protocol.
    The `read` method should return a string representation of the data read from the protocol.
    """
    def __init__(self, address: str, function, params, read_method):
        self.address = address
        self.function = function
        self.params = params
        self.read_method = read_method

    @abstractmethod
    def exists(self) -> bool:
        """
        Check if the address exists.
        This method should be implemented by subclasses to check the existence of the address.
        """
        pass

    @abstractmethod
    def read(self) -> str:
        """
        Read data from the address.
        This method should be implemented by subclasses to read data from the address.
        """
        pass


@log_method_calls()
class HTTPProtocolHandler(BaseProtocolHandler):
    """
    HTTPProtocolHandler is a subclass of BaseProtocolHandler that handles HTTP and HTTPS protocols.
    It uses the requests library to make HTTP GET requests to the specified address.
    Attributes:
        address (str): The HTTP or HTTPS address to connect to.
        function (callable): The function to call for the protocol (requests.get).
        params (dict): The parameters to pass to the function (e.g., verify=False).
        read_method (str): The method to call on the response object (e.g., text).
    """
    def exists(self) -> bool:
        try:
            response = self.function(self.address, **self.params)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def read(self) -> str:
        response = self.function(self.address, **self.params)
        return getattr(response, self.read_method)


@log_method_calls()
class FileProtocolHandler(BaseProtocolHandler):
    """
    FileProtocolHandler is a subclass of BaseProtocolHandler that handles file protocols.
    It uses the built-in open function to read files from the specified address.
    Attributes:
        address (str): The file address to connect to.
        function (callable): The function to call for the protocol (open).
        params (dict): The parameters to pass to the function (e.g., encoding, mode).
        read_method (str): The method to call on the file object (e.g., read).
    """
    def exists(self) -> bool:
        try:
            with self.function(self.address.replace("file://", ""), **self.params) as file:
                return True
        except FileNotFoundError:
            return False

    def read(self) -> str:
        with self.function(self.address.replace("file://", ""), **self.params) as file:
            return getattr(file, self.read_method)()


@log_method_calls()
class Protocol(Enum):
    """
    Enum for supported protocols. Each protocol is associated with a handler class
    and the parameters needed to handle it.
    Attributes:
        HTTP: HTTP protocol handler.
        HTTPS: HTTPS protocol handler.
        FILE: File protocol handler.
    """
    HTTP = "http://", requests.get, {"verify": False}, "text", HTTPProtocolHandler
    HTTPS = "https://", requests.get, {"verify": False}, "text", HTTPProtocolHandler
    FILE = "file://", open, {"encoding": "utf-8", "mode": "r"}, "read", FileProtocolHandler

    @property
    def protocol(self): return self.value[0]
    @property
    def function(self): return self.value[1]
    @property
    def params(self): return self.value[2]
    @property
    def read_method(self): return self.value[3]
    @property
    def handler_class(self): return self.value[4]

    @classmethod
    def from_spec_address(cls, value: "SpecAddress") -> "Protocol":
        spec_address = str(value)
        for protocol in cls:
            if spec_address.startswith(protocol.protocol):
                return protocol
        raise ValueError(f"Unsupported protocol in address: {spec_address}")
