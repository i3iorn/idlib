import json

from PyQt6.QtCore import QTimer, Qt, QMimeData, pyqtSignal
from PyQt6.QtGui import (
    QFocusEvent, QTextCursor, QTextCharFormat, QColor
)
from PyQt6.QtWidgets import QTextEdit, QToolTip

from api_viewer.json_highlighter import JsonHighlighter


class JsonTextEdit(QTextEdit):
    jsonValidityChanged = pyqtSignal(bool, str)

    def __init__(self, parent=None, indent=4, read_only=False):
        super().__init__(parent)
        self._textChangeDelay = 0
        self.indent = indent
        self.setAcceptRichText(False)
        self.setReadOnly(read_only)

        self._last_valid = None
        self._last_text_validated = ""

        # install the highlighter
        self._highlighter = JsonHighlighter(self.document())

        self._json_timer = QTimer(self)
        self._json_timer.setSingleShot(True)
        self._json_timer.timeout.connect(self._validate_json)

        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self):
        current_text = self.toPlainText()
        if current_text != self._last_text_validated:
            self._json_timer.start(self._textChangeDelay)

    def keyPressEvent(self, event):
        key = event.key()
        cursor = self.textCursor()
        block_text = cursor.block().text()
        pairs = {
            ord('{'): '}', ord('['): ']', ord('('): ')', ord('"'): '"',
        }
        if key in pairs:
            opening, closing = chr(key), pairs[key]
            cursor.insertText(opening + cursor.selectedText() + closing)
            cursor.movePosition(QTextCursor.MoveOperation.Left)
            self.setTextCursor(cursor)
            return

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            leading = len(block_text) - len(block_text.lstrip(' '))
            cursor.insertText('\n' + ' ' * leading)
            return

        if key == Qt.Key.Key_Tab:
            cursor.insertText(' ' * self.indent)
            return

        super().keyPressEvent(event)

    def _validate_json(self) -> bool:
        raw = self.toPlainText()
        self._last_text_validated = raw
        self._clear_error_formatting()

        try:
            json.loads(raw)
            valid, msg = True, ""
        except json.JSONDecodeError as e:
            valid, msg = False, e.msg
            self._show_json_error(e)

        if valid != self._last_valid:
            self._last_valid = valid
            self.jsonValidityChanged.emit(valid, msg)

        return valid

    def focusOutEvent(self, event: QFocusEvent) -> None:
        if self._validate_json():
            self._try_pretty_format()
        super().focusOutEvent(event)

    def insertFromMimeData(self, source: QMimeData) -> None:
        if source.hasText():
            raw = source.text()
            formatted = self._try_format_json(raw)
            self.textCursor().insertText(formatted)
        else:
            super().insertFromMimeData(source)

    def _try_pretty_format(self):
        raw = self.toPlainText().strip()
        pretty = self._try_format_json(raw)
        if pretty != raw:
            self.blockSignals(True)
            self.setPlainText(pretty)
            self.blockSignals(False)

    def _try_format_json(self, raw: str) -> str:
        try:
            parsed = json.loads(raw)
            return json.dumps(parsed, indent=self.indent, ensure_ascii=False)
        except Exception:
            return raw

    def _clear_error_formatting(self):
        doc = self.document()
        cursor = QTextCursor(doc)
        cursor.select(QTextCursor.SelectionType.Document)
        fmt = QTextCharFormat()
        fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.NoUnderline)
        fmt.setBackground(QColor("transparent"))
        cursor.setCharFormat(fmt)

    def _show_json_error(self, error: json.JSONDecodeError):
        pos = error.pos
        doc = self.document()
        cursor = QTextCursor(doc)
        cursor.setPosition(pos)
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)

        fmt = QTextCharFormat()
        fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)
        fmt.setUnderlineColor(QColor("red"))
        cursor.setCharFormat(fmt)

        rect = self.cursorRect(cursor)
        global_pos = self.viewport().mapToGlobal(rect.bottomRight())
        QToolTip.showText(global_pos, error.msg, self)

    def setTextChangeDelay(self, delay: int):
        self._textChangeDelay = delay

    def textChangeDelay(self):
        return self._textChangeDelay
