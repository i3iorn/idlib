from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QComboBox, QLabel, QTextEdit, QHBoxLayout

from api_viewer.central_widget.core import CentralChildWidget
from api_viewer.constants import NO_MARGIN


class ConfigWidget(CentralChildWidget):
    def _setup_ui(self):
        conf_layout = QVBoxLayout()
        conf_layout.setContentsMargins(*NO_MARGIN)
        self.combo_box_1 = QComboBox()
        self.combo_box_2 = QComboBox()
        self.combo_box_3 = QComboBox()

        # Add combo boxes to the layout
        self._api_combobox = self._add_combobox(conf_layout, "API: ", ["Option 1", "Option 2", "Option 3"])
        self._endpoint_combobox = self._add_combobox(conf_layout, "Endpoint: ", ["Option A", "Option B", "Option C"])
        self._endpoint_combobox.setDisabled(True)
        self._api_combobox.activated.connect(lambda: self._endpoint_combobox.setEnabled(True))
        self._client_combobox = self._add_combobox(conf_layout, "Client: ", ["Choice X", "Choice Y", "Choice Z"])
        self._client_combobox.setDisabled(True)
        self._api_combobox.activated.connect(lambda: self._client_combobox.setEnabled(True))

        # Add a spacer item to the layout
        conf_layout.addStretch(1)

        # Create the multiline text window (QTextEdit)
        body_label = QLabel("Body:")
        conf_layout.addWidget(body_label, alignment=Qt.AlignmentFlag.AlignTop)
        self.text_edit = QTextEdit()
        self.text_edit.setFixedHeight(150)  # ~6 rows of text
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        conf_layout.addWidget(self.text_edit, alignment=Qt.AlignmentFlag.AlignTop)

        self.setLayout(conf_layout)

    def _add_combobox(self, layout, label, items):
        """
        Add a combo box to the layout with the given label and items.
        """
        cb_layout = QHBoxLayout()
        cb_layout.setContentsMargins(*NO_MARGIN)

        label = QLabel(label)
        cb_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignTop, stretch=1)
        combo_box = QComboBox()
        combo_box.addItems(items)
        cb_layout.addWidget(combo_box, alignment=Qt.AlignmentFlag.AlignTop, stretch=3)
        layout.addLayout(cb_layout)
        return combo_box
