from PyQt6.QtWidgets import QWidget, QSizePolicy, QVBoxLayout


class CentralChildWidget(QWidget):
    def __init__(self, parent=None, layout=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setObjectName(self.__class__.__name__)
        if layout is None:
            layout = QVBoxLayout()
        self.setLayout(layout)
        self._setup_ui()

    def _setup_ui(self):
        for name, method in self.__dict__.items():
            if name.startswith("_setup_") and not name == "_setup_ui":
                method()
