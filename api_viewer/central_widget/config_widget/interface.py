from abc import ABC, abstractmethod
from typing import Any, Dict


class ApiServiceInterface(ABC):
    @abstractmethod
    async def call_api(self, api_spec: Any, path: str, client_spec: Any, payload: Dict[str, Any]) -> None:
        pass
