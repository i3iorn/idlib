from dataclasses import dataclass
from typing import Any


@dataclass
class ConfigState:
    api_spec: Any = None
    endpoint_path: str = ""
    client_spec: Any = None
    prodtest: bool = False
    external: bool = False

    def set_api_spec(self, api_spec: Any) -> None:
        self.api_spec = api_spec

    def set_endpoint(self, endpoint_path: str) -> None:
        self.endpoint_path = endpoint_path
