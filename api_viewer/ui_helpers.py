from typing import Union, Dict, Iterable

from PyQt6.QtWidgets import QBoxLayout, QWidget, QHBoxLayout, QLabel, QComboBox

from api_viewer.constants import NO_MARGIN


def add_labeled_row(layout: QBoxLayout, label_text: str, widget: QWidget, stretch: tuple = (1,3)):
    row = QHBoxLayout()
    row.setContentsMargins(*NO_MARGIN)
    row.addWidget(QLabel(label_text), stretch[0])
    row.addWidget(widget, stretch[1])
    layout.addLayout(row)

def populate_combo(combo: QComboBox, items: Union[Dict, Iterable]):
    combo.clear()
    if isinstance(items, dict):
        for name, data in items.items():
            combo.addItem(name, data)
    else:
        for item in items:
            name = getattr(item, "name", str(item))
            combo.addItem(name, item)
    combo.setCurrentIndex(0)