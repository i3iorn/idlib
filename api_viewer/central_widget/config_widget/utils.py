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
