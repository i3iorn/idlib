from typing import List, Iterator

from PyQt6.QtCore import QModelIndex, Qt, QAbstractItemModel
from PyQt6.QtWidgets import QWidget, QAbstractItemView, QLineEdit, QLabel, QHBoxLayout

from api_viewer.central_widget.core.central_child import _unwrap_model


class SearchBar(QWidget):
    """
    A search widget with previous/next buttons that walks the
    underlying model to highlight matches without hiding rows.
    """
    def __init__(self, view: QAbstractItemView, placeholder: str = "Search...", parent=None):
        super().__init__(parent)
        self._view = view
        self._line = QLineEdit()
        self._line.setPlaceholderText(placeholder)
        self._prev_btn = QLabel("↑")
        self._next_btn = QLabel("↓")

        # clickable labels hack
        self._prev_btn.mousePressEvent = lambda _: self._prev_match()
        self._next_btn.mousePressEvent = lambda _: self._next_match()
        self._line.textChanged.connect(self._on_search)

        self._results: List[QModelIndex] = []
        self._idx = -1

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        for w in (self._line, self._prev_btn, self._next_btn):
            layout.addWidget(w)

    def _on_search(self, text: str) -> None:
        self._results.clear()
        self._idx = -1
        if not text:
            return

        model = _unwrap_model(self._view.model())
        self._results = [
            idx
            for idx in self._iter_all_indices(model)
            if text.lower() in str(model.data(idx, Qt.ItemDataRole.DisplayRole)).lower()
        ]
        if self._results:
            self._idx = 0
            self._highlight_current()

    def _iter_all_indices(self, model: QAbstractItemModel) -> Iterator[QModelIndex]:
        """
        Yield every index in a simple row-major traversal.
        """
        rows = model.rowCount()
        cols = model.columnCount()
        for r in range(rows):
            for c in range(cols):
                yield model.index(r, c)

    def _highlight_current(self) -> None:
        idx = self._results[self._idx]
        self._view.scrollTo(idx, self._view.ScrollHint.PositionAtCenter)
        self._view.setCurrentIndex(idx)

    def _next_match(self) -> None:
        if not self._results:
            return
        self._idx = (self._idx + 1) % len(self._results)
        self._highlight_current()

    def _prev_match(self) -> None:
        if not self._results:
            return
        self._idx = (self._idx - 1) % len(self._results)
        self._highlight_current()
