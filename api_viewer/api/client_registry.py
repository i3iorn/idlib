import logging
from threading import Lock
from copy import deepcopy
from typing import Callable, Dict, Any, Optional

from api_viewer.log.decorator import log_method_calls

logger = logging.getLogger(__name__)


@log_method_calls()
class ClientRegistry:
    """
    Thread-safe singleton registry for API specs and associated hooks.
    This class is a singleton and should be accessed via the `get_instance` method.
    It provides methods to register, unregister, and retrieve API specs.
    It also allows for the retrieval of all registered specs.
    The registry is thread-safe, ensuring that multiple threads can access it
    without causing data corruption or inconsistencies.

    Attributes:
        _instance (ClientRegistry): The singleton instance of the registry.
        _registry (Dict[str, dict]): A dictionary mapping spec names to their respective specs.
        _lock (Lock): A threading lock to ensure thread safety.

    Methods:
        all() -> Dict[str, dict]:
            Returns a shallow copy of all registered specs.

        register(name: str, client: dict) -> None:
            Registers a spec under a given name.

        unregister(name: str) -> None:
            Removes a client by name.

        get(name: str) -> Optional[dict]:
            Returns a copy of the client for the given name.

        get_client_by_scope(scope: str) -> Optional[dict]:
            Returns a copy of the client for the given scope.

        __repr__() -> str:
            Returns a string representation of the registry.

    Example:
        registry = ClientRegistry.get_instance()
        registry.register("example_client", {"url": "https://api.example.com"})
        client = registry.get("example_client")
        print(client)
    """
    _instance = None
    _singleton_lock = Lock()

    def __new__(cls):
        """
        Create a new instance of the ClientRegistry if it doesn't exist.
        If it does exist, return the existing instance.
        This method is thread-safe to ensure that only one instance
        of the registry is created, even in a multi-threaded environment.

        Arguments:
            cls: The class itself.
        Returns:
            ClientRegistry: The singleton instance of the registry.
        Raises:
            RuntimeError: If the registry is not initialized.
        """
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        Initialize the ClientRegistry.
        This method is called only once when the instance is created.
        It sets up the registry dictionary and the lock for thread safety.
        Raises:
            RuntimeError: If the registry is not initialized.
        """
        if not self._initialized:
            self._initialized = True
            self._registry: Dict[str, dict] = {}
            self._lock = Lock()

        self.register(
            "Sandbox",
            {
                "clientId": "71a7c376-0f79-4fc5-9db9-6447d2097e21",
                "clientSecret": "Ut0dzd8PWzZpxorrFJ8l0d8D4ZcbLNHsJVncvjc26v9V7A4LlLkCAgF11jsJdOxM",
                "associatedServer": "https://login.bisnode.com/sandbox/v1/token.oauth2",
                "environment": "sandbox",
                "customerCode": "",
                "scopes": ["credit_data_companies", "credit_data_persons", "rgs-decision", "rgs-decision-test", "credit_data_companies"],
                "notes": "Björn Schrammel",
                "internalClient": True,
                "rulesetKeys": [
                    {
                        "key": "1-d758-0bd3-3464",
                        "country": "SE",
                        "channel": "b2b",
                        "notes": "Complex ruleset key for company screening"
                    },
                    {
                        "key": "1-d019-1c35-f652",
                        "country": "SE",
                        "channel": "b2b",
                        "notes": "Simple ruleset key for company screening"
                    },
                    {
                        "key": "1-adbf-552e-31d3",
                        "country": "SE",
                        "channel": "b2c"
                    }
                ]
            }
        )

    def all(self, host: str = None) -> Dict[str, dict]:
        """
        Return a shallow copy of all registered specs.
        This method is thread-safe and returns a copy of the registry
        to prevent external modifications.
        Returns:
            Dict[str, dict]: A shallow copy of all registered specs.
        Raises:
            RuntimeError: If the registry is not initialized.
        """
        if not self._initialized:
            raise RuntimeError("ClientRegistry not initialized")
        with self._lock:
            if host:
                return {
                    name: client
                    for name, client in self._registry.items()
                    if "host" in client and client["host"].lower() == host.lower()
                }
            else:
                # Return all clients if no host is specified
                logger.debug("Returning all registered clients")
                return self._registry.copy()

    def internal_clients(self, host: str = None) -> Dict[str, dict]:
        """
        Return a shallow copy of all registered internal clients.
        This method is thread-safe and returns a copy of the registry
        to prevent external modifications.
        Returns:
            Dict[str, dict]: A shallow copy of all registered internal clients.
        Raises:
            RuntimeError: If the registry is not initialized.
        """
        return {
            name: client
            for name, client in self.all(host).items()
            if client.get("internalClient", False)
        }

    def external_clients(self, host: str = None) -> Dict[str, dict]:
        """
        Return a shallow copy of all registered external clients.
        This method is thread-safe and returns a copy of the registry
        to prevent external modifications.
        Returns:
            Dict[str, dict]: A shallow copy of all registered external clients.
        Raises:
            RuntimeError: If the registry is not initialized.
        """
        return {
            name: client
            for name, client in self.all(host).items()
            if not client.get("internalClient", False)
        }

    def register(self, name: str, client: dict) -> None:
        """
        Register a spec under a given name.
        This method is thread-safe and ensures that the registry
        is not modified by multiple threads at the same time.
        Arguments:
            name (str): The name under which to register the spec.
            client (dict): The spec to register.

        Raises:
            RuntimeError: If the registry is not initialized.
            ValueError: If the name is not a string or the client is not a dictionary.
        """
        if not isinstance(client, dict):
            raise ValueError(f"Client must be a dictionary, got {type(client)}")

        with self._lock:
            self._registry[name] = client

    def unregister(self, name: str) -> None:
        """
        Remove a client by name.
        This method is thread-safe and ensures that the registry
        is not modified by multiple threads at the same time.
        Arguments:
            name (str): The name of the client to remove.

        Raises:
            RuntimeError: If the registry is not initialized.
            ValueError: If the name is not a string.
            KeyError: If the client is not found in the registry.
        """
        if not self._initialized:
            raise RuntimeError("ClientRegistry not initialized")

        if not isinstance(name, str):
            raise ValueError(f"Name must be a string, got {type(name)}")
        with self._lock:
            if name in self._registry:
                logger.debug(f"Unregistering client '{name}'")
                del self._registry[name]
            else:
                raise KeyError(f"Client '{name}' not found in registry")

    def get(self, name: str) -> Optional[dict]:
        """
        Return a copy of the client for the given name.
        This method is thread-safe and ensures that the registry
        is not modified by multiple threads at the same time.
        Arguments:
            name (str): The name of the client to retrieve.

        Returns:
            Optional[dict]: A copy of the client for the given name,
                            or None if the client is not found.

        Raises:
            RuntimeError: If the registry is not initialized.
            ValueError: If the name is not a string.
        """
        with self._lock:
            client = self._registry.get(name)
            if client is None:
                logger.debug(f"Client '{name}' not found in registry")
            else:
                logger.debug(f"Client '{name}' found in registry")
            return deepcopy(client) if client is not None else None

    def get_client_by_scope(self, scope: str) -> Optional[dict]:
        """
        Return a copy of the client for the given scope.
        This method is thread-safe and ensures that the registry
        is not modified by multiple threads at the same time.
        Arguments:
            scope (str): The scope of the client to retrieve.

        Returns:
            Optional[dict]: A copy of the client for the given scope,
                            or None if the client is not found.

        Raises:
            RuntimeError: If the registry is not initialized.
            ValueError: If the scope is not a string.
        """
        with self._lock:
            for client in self._registry.values():
                if scope in client.get("scope"):
                    logger.debug(f"Client with scope '{scope}' found in registry")
                    return deepcopy(client)
            return None

    def __repr__(self):
        with self._lock:
            keys = list(self._registry.keys())
        return f"<ClientRegistry clients={keys}>"
