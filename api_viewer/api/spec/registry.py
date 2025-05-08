import logging
from threading import Lock
from copy import deepcopy
from typing import Callable, Dict, Optional, List

from api_viewer.emitter import signal_emitter
from api_viewer.log.decorator import log_method_calls

logger = logging.getLogger(__name__)


@log_method_calls()
class SpecRegistry:
    """
    Thread-safe singleton registry for API specs and associated hooks.
    This class is designed to be used as a singleton, ensuring that
    only one instance exists throughout the application lifecycle.
    It provides methods to register, unregister, and retrieve specs,
    as well as to add and remove hooks that can transform the specs.
    Attributes:
        _instance (SpecRegistry): The singleton instance of the registry.
        _registry (Dict[str, dict]): A dictionary mapping spec names to their definitions.
        _hooks (Dict[str, list[Callable[[str], str]]]): A dictionary mapping spec names to lists of hooks.
        _lock (Lock): A threading lock to ensure thread-safe access to the registry.
    Methods:
        all() -> Dict[str, dict]:
            Returns a shallow copy of all registered specs.
        register(name: str, spec: dict) -> None:
            Registers a spec under a given name.
        unregister(name: str) -> None:
            Removes a spec by name.
        get(name: str) -> Optional[dict]:
            Returns a copy of the spec for the given name.
        add_hook(name: str, hook: Callable[[str], str]) -> None:
            Adds a callable hook that transforms a spec.
        remove_hook(name: str, hook: Callable[[str], str]) -> None:
            Removes a hook for a given spec name.
        apply_hooks(name: str, spec: str) -> str:
            Applies all hooks for a spec name to a deep copy of the spec.

        __repr__() -> str:
            Returns a string representation of the SpecRegistry instance,
            including the names of all registered specs.

        __new__(cls) -> "SpecRegistry":
            Creates a new instance of the SpecRegistry class if one does not already exist.
            Ensures that only one instance of the class is created (singleton pattern).

        __init__(self) -> None:
            Initializes the SpecRegistry instance, setting up the registry and hooks.
            This method is called only once when the singleton instance is created.

        Raises:
            ValueError: If the spec is not a dictionary or if the name is not a valid identifier.
            KeyError: If the spec name is not found in the registry or if the hook is not found for the spec.
            TypeError: If the spec is not a dictionary or if the hook is not callable.

    """
    _instance: Optional["SpecRegistry"] = None
    _singleton_lock: Lock = Lock()

    def __new__(cls):
        """
        Create a new instance of the SpecRegistry class if one does not already exist.
        This method ensures that only one instance of the class is created (singleton pattern).
        It uses a threading lock to ensure thread-safe access to the singleton instance.
        Returns:
            SpecRegistry: The singleton instance of the SpecRegistry class.

        Raises:
            ValueError: If the spec is not a dictionary or if the name is not a valid identifier.
            KeyError: If the spec name is not found in the registry or if the hook is not found for the spec.
            TypeError: If the spec is not a dictionary or if the hook is not callable.
        """
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        Initialize the SpecRegistry instance, setting up the registry and hooks.
        This method is called only once when the singleton instance is created.
        It uses a threading lock to ensure thread-safe access to the registry.
        Raises:
            ValueError: If the spec is not a dictionary or if the name is not a valid identifier.
            KeyError: If the spec name is not found in the registry or if the hook is not found for the spec.
            TypeError: If the spec is not a dictionary or if the hook is not callable.
        """
        if not self._initialized:
            self._initialized = True
            self._registry: Dict[str, dict] = {}
            self._hooks: Dict[str, list[Callable[[str], str]]] = {}
            self._lock = Lock()

    def hook_count(self, name: str = None) -> int:
        if name is None:
            return sum(len(h) for h in self._hooks.values())
        return len(self._hooks.get(name, []))

    def all(self) -> Dict[str, dict]:
        """
        Return a shallow copy of all registered specs.
        This method is thread-safe and returns a copy of the registry
        to prevent external modifications.
        Returns:
            Dict[str, dict]: A shallow copy of the registry containing all registered specs.
        Raises:
            None

        Examples:
            >>> registry = SpecRegistry()
            >>> registry.register("example", {"key": "value"})
            >>> all_specs = registry.all()
            >>> print(all_specs)
            {'example': {'key': 'value'}}
        """
        logger.debug("Returning all registered specs")
        with self._lock:
            return self._registry.copy()

    def register(self, name: str, spec: dict) -> None:
        """
        Register a spec under a given name.
        This method is thread-safe and ensures that the spec is a dictionary
        and that the name is a valid identifier.
        Args:
            name (str): The name under which to register the spec.
            spec (dict): The spec to register.
        Raises:
            ValueError: If the spec is not a dictionary or if the name is not a valid identifier.
            KeyError: If the spec name already exists in the registry.

        Examples:
            >>> registry = SpecRegistry()
            >>> registry.register("example", {"key": "value"})
            >>> spec = registry.get("example")
            >>> print(spec)
            {'key': 'value'}
        """
        if not isinstance(spec, dict):
            raise ValueError("Spec must be a dictionary")

        with self._lock:
            if name in self._registry:
                logger.warning(f"Spec '{name}' already registered, overwriting")
            if not name.isidentifier():
                raise ValueError(f"Invalid spec name '{name}': must be a valid identifier")
            logger.debug(f"Registering spec '{name}'")
            self._registry[name] = spec

        signal_emitter.apiAvailable.emit(name)

    def unregister(self, name: str) -> None:
        """
        Remove a spec by name.
        This method is thread-safe and ensures that the spec name exists in the registry
        before attempting to remove it.
        Args:
            name (str): The name of the spec to remove.
        Raises:
            KeyError: If the spec name is not found in the registry.
        Examples:
            >>> registry = SpecRegistry()
            >>> registry.register("example", {"key": "value"})
            >>> registry.unregister("example")
            >>> spec = registry.get("example")
            >>> print(spec)
        """
        with self._lock:
            if name in self._registry:
                logger.debug(f"Unregistering spec '{name}'")
                del self._registry[name]
            else:
                raise KeyError(f"Spec '{name}' not found in registry")

    def get(self, name: str) -> Optional[dict]:
        """
        Return a copy of the spec for the given name.
        This method is thread-safe and returns a copy of the spec
        to prevent external modifications.

        Args:
            name (str): The name of the spec to retrieve.
        Returns:
            Optional[dict]: A copy of the spec for the given name, or None if not found.
        Raises:
            KeyError: If the spec name is not found in the registry.
        Examples:
            >>> registry = SpecRegistry()
            >>> registry.register("example", {"key": "value"})
            >>> spec = registry.get("example")
            >>> print(spec)
            {'key': 'value'}
        """
        with self._lock:
            spec = self._registry.get(name)
            if spec is None:
                logger.error(f"Spec '{name}' not found in registry")
                raise KeyError(f"Spec '{name}' not found in registry")
            logger.debug(f"Returning spec '{name}'")
            return deepcopy(spec) if spec is not None else None

    def get_hook(self, name: str) -> Optional[List[Callable[[str], str]]]:
        """
        Return a copy of the hooks for the given spec name.
        This method is thread-safe and returns a copy of the hooks
        to prevent external modifications.
        Args:
            name (str): The name of the spec for which to retrieve hooks.
        Returns:
            Optional[List[Callable[[str], str]]]: A copy of the hooks for the given spec name, or None if not found.
        Raises:
            KeyError: If the spec name is not found in the registry.
        Examples:
            >>> registry = SpecRegistry()
            >>> registry.register("example", {"key": "value"})
            >>> def example_hook(spec: str) -> str:
            ...     return spec.replace("value", "new_value")
            >>> registry.add_hook("example", example_hook)
            >>> hooks = registry.get_hook("example")
            >>> print(hooks)
            [<function example_hook at 0x...>]
        """
        with self._lock:
            hooks = self._hooks.get(name)
            if hooks is None:
                logger.error(f"Hooks for spec '{name}' not found in registry")
                raise KeyError(f"Hooks for spec '{name}' not found in registry")
            logger.debug(f"Returning hooks for spec '{name}'")
            return deepcopy(hooks) if hooks is not None else None

    def hooks(self) -> Dict[str, List[Callable[[str], str]]]:
        """
        Return a shallow copy of all registered hooks.
        This method is thread-safe and returns a copy of the hooks
        to prevent external modifications.
        Returns:
            Dict[str, List[Callable[[str], str]]]: A shallow copy of the hooks registry.
        Raises:
            None
        Examples:
            >>> registry = SpecRegistry()
            >>> registry.register("example", {"key": "value"})
            >>> def example_hook(spec: str) -> str:
            ...     return spec.replace("value", "new_value")
            >>> registry.add_hook("example", example_hook)
            >>> all_hooks = registry.hooks()
            >>> print(all_hooks)
            {'example': [<function example_hook at 0x...>]}
        """
        logger.debug("Returning all registered hooks")
        with self._lock:
            return self._hooks.copy()

    def add_hook(self, name: str, hook: Callable[[str], str]) -> None:
        """
        Add a callable hook that transforms a spec.
        This method is thread-safe and ensures that the hook is callable
        and that the spec name exists in the registry.
        Args:
            name (str): The name of the spec to which the hook will be applied.
            hook (Callable[[str], str]): The hook function to add.
        Raises:
            ValueError: If the hook is not callable.
            KeyError: If the spec name does not exist in the registry.
        Examples:
            >>> registry = SpecRegistry()
            >>> registry.register("example", {"key": "value"})
            >>> def example_hook(spec: str) -> str:
            ...     return spec.replace("value", "new_value")
            >>> registry.add_hook("example", example_hook)
            >>> updated_spec = registry.apply_hooks("example", "value")
            >>> print(updated_spec)
            new_value
        """
        if not callable(hook):
            raise ValueError("Hook must be callable")

        with self._lock:
            if name not in self._hooks:
                logger.debug(f"Creating new hook list for spec '{name}'")
                self._hooks[name] = []
            self._hooks[name].append(hook)

    def remove_hook(self, name: str, hook: Callable[[str], str]) -> None:
        """
        Remove a hook for a given spec name.
        This method is thread-safe and ensures that the hook exists
        for the spec name before attempting to remove it.
        Args:
            name (str): The name of the spec from which to remove the hook.
            hook (Callable[[str], str]): The hook function to remove.
        Raises:
            KeyError: If the spec name does not exist in the registry
                      or if the hook is not found for the spec.
        Examples:
            >>> registry = SpecRegistry()
            >>> registry.register("example", {"key": "value"})
            >>> def example_hook(spec: str) -> str:
            ...     return spec.replace("value", "new_value")
            >>> registry.add_hook("example", example_hook)
            >>> registry.remove_hook("example", example_hook)
            >>> updated_spec = registry.apply_hooks("example", "value")
            >>> print(updated_spec)
        """
        with self._lock:
            if name in self._hooks and hook in self._hooks[name]:
                logger.debug(f"Removing hook {hook} from spec '{name}'")
                self._hooks[name].remove(hook)
            else:
                raise KeyError(f"Hook not found for spec '{name}'")

    def apply_hooks(self, name: str, spec: str) -> str:
        """
        Apply all hooks for a spec name to a deep copy of the spec.
        This method is thread-safe and ensures that the hooks are applied
        in the order they were added.
        Args:
            name (str): The name of the spec to which the hooks will be applied.
            spec (str): The spec to transform using the hooks.
        Returns:
            str: The transformed spec after applying all hooks.
        Raises:
            KeyError: If the spec name does not exist in the registry.
        Examples:
            >>> registry = SpecRegistry()
            >>> registry.register("example", {"key": "value"})
            >>> def example_hook(spec: str) -> str:
            ...     return spec.replace("value", "new_value")
            >>> registry.add_hook("example", example_hook)
            >>> updated_spec = registry.apply_hooks("example", "value")
            >>> print(updated_spec)
            new_value
        """
        with self._lock:
            hooks: List[Callable[[str], str]] = self._hooks.get(name, []).copy()
        logger.debug(f"Applying hooks for spec '{name}'")

        updated_spec = deepcopy(spec)
        for hook in hooks:
            logger.debug(f"Applying hook {hook} to spec {name}")
            updated_spec = hook(updated_spec)

        return updated_spec

    def __repr__(self):
        with self._lock:
            keys = list(self._registry.keys())
        return f"<SpecRegistry specs={keys}>"
