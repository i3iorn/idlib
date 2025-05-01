from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QComboBox, QLabel, QTextEdit, QHBoxLayout, QBoxLayout

from api_viewer.central_widget.core import CentralChildWidget
from api_viewer.constants import NO_MARGIN


class ConfigWidget(CentralChildWidget):
    def _setup_ui(self):
        self.comboboxes = {}
        self.comboboxes["api"] = self._create_combobox("API:")
        self.comboboxes["api"].activated.connect(self._on_api_changed)

        self.comboboxes["endpoint"] = self._create_combobox("Endpoint:")
        self.comboboxes["client"] = self._create_combobox("Client:")

        for name, spec in self.spec_registry.all().items():
            self.comboboxes["api"].addItem(name)
            self.comboboxes["api"].setItemData(self.comboboxes["api"].count() - 1, spec, Qt.ItemDataRole.BackgroundRole)

        for cb in self.comboboxes.values():
            cb.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
            cb.setDuplicatesEnabled(False)
            cb.setMaxVisibleItems(10)
            cb.setMinimumContentsLength(20)

        # Add a spacer item to the layout
        self.layout().addStretch(1)

        # Create the multiline text window (QTextEdit)
        body_label = QLabel("Body:")
        self.layout().addWidget(body_label, alignment=Qt.AlignmentFlag.AlignTop)
        self.text_edit = QTextEdit()
        self.text_edit.setFixedHeight(150)  # ~6 rows of text
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.layout().addWidget(self.text_edit, alignment=Qt.AlignmentFlag.AlignTop)

    def _create_combobox(self, label):
        """
        Add a combo box to the layout with the given label and items.
        """
        cb_layout = QHBoxLayout()
        cb_layout.setContentsMargins(*NO_MARGIN)

        label = QLabel(label)
        cb_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignTop, stretch=1)
        combo_box = QComboBox()
        cb_layout.addWidget(combo_box, alignment=Qt.AlignmentFlag.AlignTop, stretch=3)
        self.layout().addLayout(cb_layout)
        return combo_box

    def _on_api_changed(self, index):
        """
        Handle the API selection change.
        """
        api_spec = self.comboboxes["api"].itemData(index, Qt.ItemDataRole.BackgroundRole)
        self.comboboxes["endpoint"].clear()
        for path, spec in api_spec["paths"].items():
            self.comboboxes["endpoint"].addItem(path)
            self.comboboxes["endpoint"].setItemData(self.comboboxes["endpoint"].count() - 1, spec, Qt.ItemDataRole.BackgroundRole)

