from copy import deepcopy
from functools import lru_cache
from typing import Optional, Any

from api_viewer.central_widget.config_widget.utils import JsonDict, _merge_schemas
from api_viewer.log.decorator import log_method_calls


@log_method_calls()
class SchemaResolver:
    def __init__(self, api_spec: JsonDict) -> None:
        self.api_spec = api_spec

    def get_schema(self, endpoint_spec: JsonDict, method: Optional[str] = None) -> Optional[JsonDict]:
        """
        Get the combined schema of parameters and request body for a given endpoint.

        If `method` is None, all methods will be considered.
        """
        methods = [method.lower()] if method else endpoint_spec.keys()
        all_schemas = {}

        for m in methods:
            method_spec = endpoint_spec.get(m)
            if not method_spec:
                continue

            combined_schema = {
                "parameters": [],
                "requestBody": None
            }

            # Collect parameters (query, path, header, cookie)
            parameters = method_spec.get("parameters", [])
            for param in parameters:
                resolved_param = self._resolve_refs(deepcopy(param))
                combined_schema["parameters"].append(resolved_param)

            # Collect request body (if exists)
            request_body = method_spec.get("requestBody", {})
            content = request_body.get("content", {})
            app_json = content.get("application/json")
            if app_json and "schema" in app_json:
                resolved_body = self._resolve_refs(deepcopy(app_json["schema"]))
                combined_schema["requestBody"] = resolved_body

            all_schemas[m] = combined_schema

        return all_schemas or None

    def get_component_schema(self, component_name: str) -> Optional[JsonDict]:
        if not component_name:
            return None
        components = self.api_spec.get("components", {}).get("schemas", {})
        return components.get(component_name) or next(
            (deepcopy(s) for name, s in components.items() if name.endswith(component_name)),
            None,
        )

    def _resolve_refs(self, node: Any) -> Any:
        if isinstance(node, list):
            return [self._resolve_refs(item) for item in node]
        if isinstance(node, dict):
            if all_of := node.pop("allOf", []):
                merged = {}
                for subschema in all_of:
                    merged = _merge_schemas(merged, self._resolve_refs(subschema))
                return self._resolve_refs(_merge_schemas(merged, node))
            if ref := node.get("$ref"):
                if ref.startswith("#/components/schemas/"):
                    name = ref.rsplit("/", 1)[-1]
                    comp = self._get_cached_component(name)
                    return deepcopy(comp) if comp else {}
                return {}
            return {k: self._resolve_refs(v) for k, v in node.items()}
        return node

    @lru_cache(maxsize=None)
    def _get_cached_component(self, name: str) -> Optional[JsonDict]:
        raw = self.get_component_schema(name)
        return self._resolve_refs(raw) if raw else None
