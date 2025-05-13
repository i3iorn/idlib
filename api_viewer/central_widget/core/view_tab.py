from PyQt6.QtCore import QAbstractItemModel
from PyQt6.QtWidgets import QWidget, QAbstractItemView, QVBoxLayout, QHBoxLayout

from api_viewer.central_widget.core.filter_bar import FilterBar
from api_viewer.central_widget.core.search_bar import SearchBar
from api_viewer.log.decorator import log_method_calls


@log_method_calls()
class ViewTab(QWidget):
    """
    Combines a view, its model, a SearchBar, and a FilterBar.
    """
    def __init__(
        self,
        view: QAbstractItemView,
        model: QAbstractItemModel,
        enable_search: bool = True,
        enable_filter: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.view = view
        self.model = model

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # control bars
        ctrl = QHBoxLayout()
        ctrl.setContentsMargins(0, 0, 0, 0)
        if enable_search:
            self.search = SearchBar(view)
            ctrl.addWidget(self.search)
        if enable_filter:
            self.filter = FilterBar(view)
            self.filter.update_model(model)
            ctrl.addWidget(self.filter)
        layout.addLayout(ctrl)
        layout.addWidget(view)
