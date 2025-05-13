from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QComboBox, QPushButton, QCheckBox

from api_viewer.log.decorator import log_method_calls


@log_method_calls()
class WidgetFactory:
    @classmethod
    def widget(cls, widget_type: QObject, *args, **kwargs):
        """
        Factory method to create a widget based on the type.
        """
        widget_types = {
            QComboBox: cls.combo,
            QPushButton: cls.button,
            QCheckBox: cls.checkbox,
        }
        if widget_type in widget_types:
            return widget_types[widget_type](*args, **kwargs)
        else:
            raise ValueError(f"Unknown widget type: {widget_type}")

    @staticmethod
    def combo() -> QComboBox:
        c = QComboBox()
        c.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
        c.setDuplicatesEnabled(False)
        c.setMaxVisibleItems(10)
        c.setMinimumContentsLength(20)
        return c

    @staticmethod
    def button(label: str, height: int = 30) -> QPushButton:
        btn = QPushButton(label)
        btn.setFixedHeight(height)
        return btn

    @staticmethod
    def checkbox() -> QCheckBox:
        return QCheckBox()
