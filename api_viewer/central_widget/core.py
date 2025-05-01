from PyQt6.QtWidgets import QWidget, QSizePolicy, QVBoxLayout

from api_viewer.api import SpecRegistry
from api_viewer.constants import NO_MARGIN


class CentralChildWidget(QWidget):
    def __init__(self, parent=None, layout=None):
        super().__init__(parent)
        self.spec_registry = SpecRegistry()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setObjectName(self.__class__.__name__)
        if layout is None:
            layout = QVBoxLayout()
        layout.setContentsMargins(*NO_MARGIN)
        self.setLayout(layout)
        self._setup_ui()

    def _setup_ui(self):
        for name in dir(self):
            if name.startswith("_setup_") and name != "_setup_ui":
                method = getattr(self, name)
                if callable(method):
                    method()
