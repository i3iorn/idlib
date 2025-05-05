import re

from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import (
    QColor, QFont, QTextCharFormat, QSyntaxHighlighter, QTextDocument, QPalette
)
from PyQt6.QtWidgets import QApplication


class JsonHighlighter(QSyntaxHighlighter):
    """
    JSON highlighter aware of light/dark mode, with precise value matching.
    Highlights:
      - Braces/brackets
      - Quotes
      - Commas/colons
      - Property names
      - ISO datetimes
      - ISO dates
      - All-uppercase constants
      - Generic strings
      - Numbers
      - Booleans & null
    """
    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)
        self._rules = []  # list of (regex, fmt, group_index)

        # Theme detection
        app = QApplication.instance()
        base = (app.palette() if app else QPalette()).color(QPalette.ColorRole.Base)
        dark = base.lightness() < 128

        # Subtle palettes
        if dark:
            pal = {
                'brace':    '#6c6c6c',
                'quote':    '#6c6c6c',
                'sep':      '#5f7d9a',
                'key':      '#ffd966',
                'datetime': '#56b6c2',
                'date':     '#98c379',
                'upper':    '#ffb86c',
                'string':   '#a9dc76',
                'number':   '#f8f8f2',
                'bool':     '#ff79c6',
            }
        else:
            pal = {
                'brace':    '#888888',
                'quote':    '#888888',
                'sep':      '#707070',
                'key':      '#b03060',
                'datetime': '#008b8b',
                'date':     '#006400',
                'upper':    '#b22222',
                'string':   '#006400',
                'number':   '#00008b',
                'bool':     '#8b008b',
            }

        # 1) Braces/brackets
        fmt = QTextCharFormat(); fmt.setForeground(QColor(pal['brace']))
        self._add(r'[\{\}\[\]]', fmt)

        # 2) Quotes as punctuation
        fmt = QTextCharFormat(); fmt.setForeground(QColor(pal['quote']))
        self._add(r'"', fmt)

        # 3) Separators: commas/colons
        fmt = QTextCharFormat(); fmt.setForeground(QColor(pal['sep']))
        self._add(r'[,:]', fmt)

        # 4) Keys: "key":
        fmt = QTextCharFormat(); fmt.setForeground(QColor(pal['key'])); fmt.setFontWeight(QFont.Weight.Bold)
        self._add(r'"(?:\\.|[^"\\])*"(?=\s*:)', fmt)

        # Value rules use capture group 1, pattern WITHOUT quotes
        # Helper to add value rule: anchored after colon, before comma/bracket
        def add_value_rule(core, color_key, ci=False):
            fmt = QTextCharFormat(); fmt.setForeground(QColor(pal[color_key]))
            # (?<=:)"(core)"(?=\s*[,}\]])
            pattern = rf'(?<=:)"({core})"(?=\s*[,\}}\]])'
            self._add(pattern, fmt, group=1, case_insensitive=ci)
            # also allow space after colon
            pattern2 = rf'(?<=: )"({core})"(?=\s*[,\}}\]])'
            self._add(pattern2, fmt, group=1, case_insensitive=ci)

        # 5) ISO datetime
        dt = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+\-]\d{2}:\d{2})?'
        add_value_rule(dt, 'datetime')

        # 6) ISO date
        date = r'\d{4}-\d{2}-\d{2}'
        add_value_rule(date, 'date')

        # 7) All uppercase constants
        add_value_rule(r'[A-Z0-9_]{2,}', 'upper')

        # 8) Generic strings (catch-all for other strings)
        fmt = QTextCharFormat(); fmt.setForeground(QColor(pal['string']))
        # match "..." not followed by colon and before comma/bracket
        self._add(r'(?<=:)"((?:\\.|[^"\\])*)"(?=\s*[,\}}\]])', fmt, group=1)
        self._add(r'(?<=: )"((?:\\.|[^"\\])*)"(?=\s*[,\}}\]])', fmt, group=1)

        # 9) Numbers
        fmt = QTextCharFormat(); fmt.setForeground(QColor(pal['number']))
        self._add(r'\b-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b', fmt)

        # 10) Booleans/null
        fmt = QTextCharFormat(); fmt.setForeground(QColor(pal['bool']))
        self._add(r'\b(?:true|false|null)\b', fmt, case_insensitive=True)

    def _add(self, pattern: str, fmt: QTextCharFormat,
             group: int = 0, case_insensitive: bool = False) -> None:
        regex = QRegularExpression(pattern)
        opts = QRegularExpression.PatternOption(0)
        if case_insensitive:
            opts |= QRegularExpression.PatternOption.CaseInsensitiveOption
        regex.setPatternOptions(opts)
        self._rules.append((regex, fmt, group))

    def highlightBlock(self, text: str) -> None:
        for regex, fmt, grp in self._rules:
            it = regex.globalMatch(text)
            while it.hasNext():
                m = it.next()
                start = m.capturedStart(grp)
                length = m.capturedLength(grp)
                if start >= 0 and length > 0:
                    self.setFormat(start, length, fmt)
