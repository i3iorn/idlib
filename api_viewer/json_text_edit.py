import json
from copy import deepcopy

from PyQt6.QtCore import QModelIndex, QAbstractListModel, QTimer, Qt, QMimeData, pyqtSignal
from PyQt6.QtGui import QFocusEvent, QTextCursor, QTextCharFormat, QColor
from PyQt6.QtWidgets import QTextEdit, QToolTip

from api_viewer.json_highlighter import JsonHighlighter

class JsonTextModel(QAbstractListModel):
    """
    QAbstractListModel wrapper for JSON text.
    Holds a single text blob and provides validation/formatting via roles.
    """

    JsonRole = Qt.ItemDataRole.UserRole + 1
    ValidRole = Qt.ItemDataRole.UserRole + 2
    ErrorRole = Qt.ItemDataRole.UserRole + 3

    def __init__(self, indent: int = 4, parent=None):
        super().__init__(parent)
        self._last_error = None
        self._last_valid = None
        self._text = ""
        self._indent = indent

    def rowCount(self, parent=QModelIndex()) -> int:
        return 1  # single-item model

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() != 0:
            return None

        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole, self.JsonRole):
            return self._text
        if role == self.ValidRole:
            return self._last_valid
        if role == self.ErrorRole:
            return self._last_error
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid() or index.row() != 0 or role not in (Qt.ItemDataRole.EditRole, self.JsonRole):
            return False
        if value != self._text:
            self._text = value
            try:
                json.loads(self._text)
                self._last_valid = True
                self._last_error = ""
            except json.JSONDecodeError as e:
                self._last_valid = False
                self._last_error = e.msg

            # notify that both text and validity roles changed
            self.dataChanged.emit(index, index, [role, self.ValidRole, self.ErrorRole])
        return True

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return (Qt.ItemFlag.ItemIsSelectable |
                Qt.ItemFlag.ItemIsEnabled |
                Qt.ItemFlag.ItemIsEditable)

    def format_on_paste(self, raw: str) -> str:
        try:
            obj = json.loads(raw)
            return json.dumps(obj, indent=self._indent, ensure_ascii=False)
        except json.JSONDecodeError:
            return raw



class JsonTextEdit(QTextEdit):
    """
    QTextEdit-based view that delegates JSON logic to JsonTextModel.
    """
    jsonValidityChanged = pyqtSignal(bool, str)

    def __init__(self, parent=None, indent=4, read_only=False, delay_ms=0):
        super().__init__(parent)
        self.setAcceptRichText(False)
        self.setReadOnly(read_only)
        self.indent = indent

        # model holds and validates text
        self._model = JsonTextModel(indent=indent)
        self._delay = delay_ms
        self._last_validated = ""

        # syntax highlighter
        self._highlighter = JsonHighlighter(self.document())

        # debounce timer for validation
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._validate)

        # connect view events
        self.textChanged.connect(self._on_text_changed)

        # listen for model changes if needed
        # e.g., to revert external updates

    def _on_text_changed(self):
        text = self.toPlainText()
        idx = self._model.index(0, 0)
        self._model.setData(idx, text, JsonTextModel.JsonRole)
        if text != self._last_validated:
            self._timer.start(self._delay)

    def _validate(self):
        idx = self._model.index(0, 0)
        self._last_validated = self._model.data(
            idx, JsonTextModel.JsonRole
        )
        valid = self._model.data(idx, JsonTextModel.ValidRole)
        msg = self._model.data(idx, JsonTextModel.ErrorRole) or ""
        self._clear_error_formatting()
        if not valid:
            self._show_error(msg)
        self.jsonValidityChanged.emit(valid or True, msg)
        return valid

    def focusOutEvent(self, event: QFocusEvent):
        self.updateFormat()
        super().focusOutEvent(event)

    def updateFormat(self):
        if self._validate():
            self._pretty_format()

    def _pretty_format(self):
        try:
            obj = json.loads(self._model.data(self._model.index(0, 0), JsonTextModel.JsonRole))
            formatted = json.dumps(obj, indent=self.indent, ensure_ascii=False)
        except json.JSONDecodeError:
            formatted = self._model.data(self._model.index(0, 0), JsonTextModel.JsonRole)

        if formatted != self.toPlainText().strip():
            self.blockSignals(True)
            self.setPlainText(formatted)
            self.blockSignals(False)

    def insertFromMimeData(self, source: QMimeData):
        if source.hasText():
            idx = self._model.index(0, 0)
            formatted = self._model.format_on_paste(source.text())
            self.textCursor().insertText(formatted)
        else:
            super().insertFromMimeData(source)

    def keyPressEvent(self, event):
        key = event.key()
        cursor = self.textCursor()
        line = cursor.block().text()
        leading = len(line) - len(line.lstrip(' '))

        pairs = {ord('{'): '}', ord('['): ']', ord('('): ')', ord('"'): '"'}
        if key in pairs:
            opening, closing = chr(key), pairs[key]
            snippet = opening
            moves = 1
            if key == ord('{'):
                snippet += f"\n{' '*(leading+1)}\n{closing}"
                moves = 2
            else:
                snippet += closing
            cursor.insertText(snippet)
            cursor.movePosition(QTextCursor.MoveOperation.Left, n=moves)
            self.setTextCursor(cursor)
            return

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            cursor.insertText('\n' + ' '*leading)
            return

        if key == Qt.Key.Key_Tab:
            cursor.insertText(' ' * self.indent)
            return

        super().keyPressEvent(event)

    def setModel(self, model: QAbstractListModel):
        """
        Set the model for this view.
        """
        self._model = model
        self._model.setData(self._model.index(0, 0), self.toPlainText(),
                            JsonTextModel.JsonRole)

    def model(self):
        """
        Get the model for this view.
        """
        return self._model

    def _clear_error_formatting(self):
        cursor = QTextCursor(self.document())
        cursor.select(QTextCursor.SelectionType.Document)
        fmt = QTextCharFormat()
        fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.NoUnderline)
        fmt.setBackground(QColor('transparent'))
        cursor.setCharFormat(fmt)

    def _show_error(self, msg: str):
        cursor = self.textCursor()
        fmt = QTextCharFormat()
        fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)
        fmt.setUnderlineColor(QColor('red'))
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.setCharFormat(fmt)

        rect = self.cursorRect(cursor)
        pos = self.viewport().mapToGlobal(rect.bottomRight())
        QToolTip.showText(pos, msg, self)

    def setTextChangeDelay(self, ms: int):
        self._delay = ms

    def textChangeDelay(self) -> int:
        return self._delay
