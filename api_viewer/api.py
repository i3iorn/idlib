import asyncio
import json
import os
from threading import Lock
from time import sleep
from enum import Enum

import yaml
import requests

from api_essentials import APIFactory
from api_essentials.auth import OAuth2Auth, ClientCredentials


class SpecRegistry:
    _instance = None
    _registry = {}
    _hooks = {}
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SpecRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._registry = {}

    def register(self, name, spec):
        if not isinstance(spec, dict):
            raise ValueError("Spec must be a dictionary")
        with self._lock:
            self._registry[name] = spec

    def unregister(self, name):
        with self._lock:
            if name in self._registry:
                del self._registry[name]
            else:
                raise KeyError(f"Spec '{name}' not found in registry")

    def get(self, key):
        with self._lock:
            return self._registry.get(key)


class SpecAddress:
    def __init__(self, spec_address: str) -> None:
        if not isinstance(spec_address, str):
            raise ValueError

        self._raw = spec_address

    def __str__(self):
        return self._raw


class Protocol(Enum):
    HTTP = "http://", requests.get, {"verify": False}, "text"
    HTTPS = "https://", requests.get, {"verify": False}, "text"
    FILE = "file://", open, {"encoding": "utf-8", "mode": "r"}, "read"

    @property
    def protocol(self):
        return self.value[0]

    @property
    def function(self):
        return self.value[1]

    @property
    def params(self):
        return self.value[2]

    @property
    def read_method(self):
        return self.value[3]

    @classmethod
    def from_spec_address(cls, value: SpecAddress) -> "Protocol":
        # Get the raw string from SpecAddress
        spec_address = str(value)

        # Check for the protocol prefix in the spec_address
        if spec_address.startswith(cls.HTTP.protocol):
            return cls.HTTP
        elif spec_address.startswith(cls.HTTPS.protocol):
            return cls.HTTPS
        elif spec_address.startswith(cls.FILE.protocol):
            return cls.FILE
        else:
            raise ValueError(f"Unsupported protocol in address: {spec_address}")

class SpecReader:
    def __init__(self, spec_address: str) -> None:
        self._address = SpecAddress(spec_address)
        self._protocol = Protocol.from_spec_address(self._address)
        self._function = self._protocol.function
        self._params = self._protocol.params
        self._read_method = self._protocol.read_method

    def read(self):
        if self._protocol == Protocol.FILE:
            # File read operation for C protocol
            with self._function(self._address._raw, **self._params) as file:
                content = getattr(file, self._read_method)()
        elif self._protocol in [Protocol.HTTP, Protocol.HTTPS]:
            # HTTP/HTTPS request operation
            response = self._function(self._address._raw, **self._params)
            content = getattr(response, self._read_method)
        else:
            raise ValueError(f"Unsupported protocol: {self._protocol}")

        return content


def load_apis():
    registry = SpecRegistry()
    with open("api_specs.ini", "r", encoding="utf-8") as spec_address_file:
        spec_addresses = spec_address_file.readlines()

    for name, spec_address in (line.strip().split("=") for line in spec_addresses):
        spec_reader = SpecReader(spec_address)
        spec_text = spec_reader.read()
        if spec_address.endswith("json"):
            spec = json.loads(spec_text)
        elif spec_address.endswith("yaml"):
            spec = yaml.safe_load(spec_text)
        else:
            raise ValueError(f"Unsupported file format: {spec_address}")
        registry.register(name, spec)



# credentials = ClientCredentials(
#     client_id="71a7c376-0f79-4fc5-9db9-6447d2097e21",
#     client_secret="Ut0dzd8PWzZpxorrFJ8l0d8D4ZcbLNHsJVncvjc26v9V7A4LlLkCAgF11jsJdOxM",
#     scopes=["rgs-decision"]
# )
# endpoint = my_api.endpoints[0]

# async def call():
#     response = await my_api.request(
#         auth_info=credentials,
#         endpoint=endpoint,
#         **{
#             "duns": 912345678
#         }
#     )
#     response.print_http()


if __name__ == "__main__":
    load_apis()
    spec_registry = SpecRegistry()
    spec = spec_registry.get("decisioning")
    my_api = APIFactory.from_openapi(spec, auth=OAuth2Auth(r"https://login.bisnode.com/sandbox/v1/token.oauth2"), verify=False, host_prefix="sandbox-")
