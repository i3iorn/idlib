from abc import ABC, abstractmethod
from typing import Any, Dict

from api_viewer.log.decorator import log_method_calls


class ApiServiceError(Exception):
    """Custom exception for API service errors."""
    pass


class ApiServiceInterface(ABC):
    @abstractmethod
    async def call_api(self, api_spec: Any, path: str, client_spec: Any, payload: Dict[str, Any]) -> None:
        pass


@log_method_calls()
class ApiService(ApiServiceInterface):
    def __init__(self, handler):
        self._handler = handler

    async def call_api(self, api_spec: Any, path: str, client_spec: Any, payload: Dict[str, Any]) -> None:
        await self._handler.call(api_spec, path, client_spec, payload)
