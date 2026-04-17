from qtpy.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor, qRgb
from qtpy.QtCore import Qt
import re


# TODO - complete this! This is currently only an example that can highlight "def" statements, but should be able to fully make it a Python syntax highlighter
class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        QSyntaxHighlighter.__init__(self, parent)

        self._mappings = {}

        class_format = QTextCharFormat()
        class_format.setFontWeight(QFont.Weight.Bold)
        class_format.setForeground(QColor(qRgb(66, 135, 245)))
        pattern = r"^\s*def\s+\w+\(.*$"
        self.add_mapping(pattern, class_format)

    def add_mapping(self, pattern, format):
        self._mappings[pattern] = format

    def highlightBlock(self, text):
        for pattern, format in self._mappings.items():
            for match in re.finditer(pattern, text):
                start, end = match.span()
                self.setFormat(start, end - start, format)
