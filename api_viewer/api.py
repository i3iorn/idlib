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

from abc import ABC, abstractmethod

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

    def add_hook(self, name, hook) -> None:
        if not callable(hook):
            raise ValueError("Hook must be callable")
        with self._lock:
            if name not in self._hooks:
                self._hooks[name] = []
            self._hooks[name].append(hook)

    def remove_hook(self, name, hook) -> None:
        with self._lock:
            if name in self._hooks and hook in self._hooks[name]:
                self._hooks[name].remove(hook)
            else:
                raise KeyError(f"Hook '{hook}' not found for spec '{name}'")

    def apply_hooks(self, name, spec):
        with self._lock:
            if name in self._hooks:
                for hook in self._hooks[name]:
                    spec = hook(spec)

        return spec

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


class SpecReader:
    def __init__(self, spec_address: str) -> None:
        self._address = SpecAddress(spec_address)
        self._protocol = Protocol.from_spec_address(self._address)
        self._handler = self._protocol.handler_class(
            str(self._address),
            self._protocol.function,
            self._protocol.params,
            self._protocol.read_method
        )

    def read(self) -> str:
        return self._handler.read()


def load_apis():
    registry = SpecRegistry()
    with open("api_specs.ini", "r", encoding="utf-8") as spec_address_file:
        spec_addresses = spec_address_file.readlines()

    for name, spec_address in (line.strip().split("=") for line in spec_addresses):
        spec_reader = SpecReader(spec_address)
        spec_text = spec_reader.read()

        spec_text = registry.apply_hooks(name, spec_text)

        if spec_address.endswith("json"):
            spec = json.loads(spec_text)
        elif spec_address.endswith("yaml"):
            spec = yaml.safe_load(spec_text)
        else:
            raise ValueError(f"Unsupported file format: {spec_address}")
        registry.register(name, spec)

async def call(spec):
    my_api = APIFactory.from_openapi(spec, auth=OAuth2Auth(r"https://login.bisnode.com/sandbox/v1/token.oauth2"), verify=False, host_prefix="sandbox-")
    response = await my_api.request(
        auth_info=ClientCredentials(
            client_id="71a7c376-0f79-4fc5-9db9-6447d2097e21",
            client_secret="Ut0dzd8PWzZpxorrFJ8l0d8D4ZcbLNHsJVncvjc26v9V7A4LlLkCAgF11jsJdOxM",
            scopes=["credit_data_persons"]
        ),
        endpoint=my_api.get_endpoint("/persons/fi/credit-data"),
        **{
            "nationalIdentificationNumber": "010113A953J",
            "reportType": "LARGE",
            "reasonCode": "1 (Application for credit)"
        }
    )
    response.print_http()

if __name__ == "__main__":
    spec_registry = SpecRegistry()

    def decisioning_fix(spec: str) -> str:
        return spec.replace("""content:
            application/json:
              schema:
                oneOf:
                  - $ref: '#/components/schemas/NonCreditDecision-api-v3-b2c-background_BackgroundDataB2CSE'
              examples:
""", "").replace("User comment", "string")

    spec_registry.add_hook(
        "decisioning",
        decisioning_fix
    )

    load_apis()
    spec = spec_registry.get("credit_b2c")
    asyncio.run(call(spec))
