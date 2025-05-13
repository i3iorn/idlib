from copy import deepcopy
from enum import Enum
from typing import Dict, Any

from PyQt6.QtWidgets import QComboBox, QPushButton, QCheckBox

JsonDict = Dict[str, Any]


class ControlKey(Enum):
    API = "api"
    ENDPOINT = "endpoint"
    CLIENT = "client"
    PRODTEST = "prodtest"
    EXTERNAL = "external"

class ControlKeyType(Enum):
    API = QComboBox
    ENDPOINT = QComboBox
    CLIENT = QComboBox
    PRODTEST = QCheckBox
    EXTERNAL = QCheckBox


def _merge_schemas(base: JsonDict, override: JsonDict) -> JsonDict:
    result = deepcopy(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _merge_schemas(result[key], val)
        elif key in result and isinstance(result[key], list) and isinstance(val, list):
            result[key] = result[key] + [v for v in val if v not in result[key]]
        else:
            result[key] = deepcopy(val)
    return result


_BODY_LABEL       = "Body:"
_JSON_DELAY_MS   = 500
_SUCCESS_STYLE   = "color: green;"
_ERROR_STYLE     = "color: red;"
_INVALID_JSON_TXT= "Invalid JSON format."
