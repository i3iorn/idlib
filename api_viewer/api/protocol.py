from abc import ABC, abstractmethod
from enum import Enum

import requests

from api_viewer.api.spec.address import SpecAddress


class BaseProtocolHandler(ABC):
    def __init__(self, address: str, function, params, read_method):
        self.address = address
        self.function = function
        self.params = params
        self.read_method = read_method

    @abstractmethod
    def read(self) -> str:
        pass


class HTTPProtocolHandler(BaseProtocolHandler):
    def read(self) -> str:
        response = self.function(self.address, **self.params)
        return getattr(response, self.read_method)


class FileProtocolHandler(BaseProtocolHandler):
    def read(self) -> str:
        with self.function(self.address.replace("file://", ""), **self.params) as file:
            return getattr(file, self.read_method)()


class Protocol(Enum):
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
