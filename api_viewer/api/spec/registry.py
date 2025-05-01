import inspect
from threading import Lock
from copy import deepcopy
from typing import Callable, Dict, Any, Optional


class SpecRegistry:
    """
    Thread-safe singleton registry for API specs and associated hooks.
    """
    _instance = None
    _singleton_lock = Lock()

    def __new__(cls):
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._registry: Dict[str, dict] = {}
            self._hooks: Dict[str, list[Callable[[dict], dict]]] = {}
            self._lock = Lock()

    def all(self) -> Dict[str, dict]:
        """
        Return a shallow copy of all registered specs.
        """
        with self._lock:
            return self._registry.copy()

    def register(self, name: str, spec: dict) -> None:
        """
        Register a spec under a given name.
        """
        if not isinstance(spec, dict):
            raise ValueError("Spec must be a dictionary")

        with self._lock:
            self._registry[name] = spec

    def unregister(self, name: str) -> None:
        """
        Remove a spec by name.
        """
        with self._lock:
            if name in self._registry:
                del self._registry[name]
            else:
                raise KeyError(f"Spec '{name}' not found in registry")

    def get(self, name: str) -> Optional[dict]:
        """
        Return a copy of the spec for the given name.
        """
        with self._lock:
            spec = self._registry.get(name)
            return deepcopy(spec) if spec is not None else None

    def add_hook(self, name: str, hook: Callable[[dict], dict]) -> None:
        """
        Add a callable hook that transforms a spec.
        """
        if not callable(hook):
            raise ValueError("Hook must be callable")

        with self._lock:
            if name not in self._hooks:
                self._hooks[name] = []
            self._hooks[name].append(hook)

    def remove_hook(self, name: str, hook: Callable[[dict], dict]) -> None:
        """
        Remove a hook for a given spec name.
        """
        with self._lock:
            if name in self._hooks and hook in self._hooks[name]:
                self._hooks[name].remove(hook)
            else:
                raise KeyError(f"Hook not found for spec '{name}'")

    def apply_hooks(self, name: str, spec: dict) -> dict:
        """
        Apply all hooks for a spec name to a deep copy of the spec.
        """
        with self._lock:
            hooks = self._hooks.get(name, []).copy()

        updated_spec = deepcopy(spec)
        for hook in hooks:
            updated_spec = hook(updated_spec)

        return updated_spec

    def __repr__(self):
        with self._lock:
            keys = list(self._registry.keys())
        return f"<SpecRegistry specs={keys}>"
