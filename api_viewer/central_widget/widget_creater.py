from PyQt6.QtWidgets import QSizePolicy, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QCheckBox

from api_viewer.constants import NO_MARGIN


@log_method_calls()
class WidgetCreator:
    @classmethod
    def create_widget(cls, widget_class, parent=None):
        """
        Create a widget of the specified class.
        """
        widget = widget_class(parent)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        return widget

    @classmethod
    def created_labeled_widget(cls, widget_class, label_text: str, layout: QVBoxLayout):
        """
        Create a labeled widget of the specified class.
        """
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(*NO_MARGIN)

        label = QLabel(label_text)
        widget = cls.create_widget(widget_class)

        h_layout.addWidget(label, 1)
        h_layout.addWidget(widget, 3)
        layout.addLayout(h_layout)

        return widget

    @classmethod
    def create_labeled_combobox(cls, label_text: str, layout: QVBoxLayout) -> QComboBox:
        """
        Create a labeled combo box.
        """
        return cls.created_labeled_widget(QComboBox, label_text, layout)

    @classmethod
    def create_labeled_checkbox(cls, label_text: str, layout: QVBoxLayout) -> QCheckBox:
        """
        Create a labeled checkbox.
        """
        return cls.created_labeled_widget(QCheckBox, label_text, layout)
