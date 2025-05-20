from PyQt6.QtCore import QSortFilterProxyModel, Qt, QAbstractItemModel
from PyQt6.QtWidgets import QLineEdit, QAbstractItemView

from api_viewer.central_widget.core.central_child import _unwrap_model
from api_viewer.log.decorator import log_method_calls


@log_method_calls()
class FilterBar(QLineEdit):
    """
    A line edit that filters rows in any QAbstractItemView via
    a QSortFilterProxyModel.
    """
    def __init__(self, target_view: QAbstractItemView, placeholder: str = "Filter...", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self._view = target_view
        self._proxy = QSortFilterProxyModel(self)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.textChanged.connect(self._proxy.setFilterFixedString)
        self._reset_proxy()

    def _reset_proxy(self) -> None:
        source = _unwrap_model(self._view.model())
        self._proxy.setSourceModel(source)
        self._view.setModel(self._proxy)

    def update_model(self, new_model: QAbstractItemModel) -> None:
        """
        Call this if the underlying source model changes completely.
        """
        self._proxy.setSourceModel(new_model)
        self._view.setModel(self._proxy)
