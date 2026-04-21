"""
Syntax highlighting for the PAGOS GUI. Almost all of this is verbatim copied from https://wiki.python.org/python/PyQt(2f)Python(20)syntax(20)highlighting.html.
The author, David Boddie, wrote the code for use with Qt2, whereas this should work with Qt6. The only modifications I have made are those necessary for the
Qt6 compatibility and stylistic choices. The code was distributed under the Modified BSD License.
"""

from qtpy.QtGui import (
    QSyntaxHighlighter,
    QTextCharFormat,
    QFont,
    QColor,
    QTextDocument,
)
from qtpy.QtCore import QRegularExpression


def format(color, style=""):
    """Return a QTextCharFormat with the given attributes."""
    _color = QColor()
    _color.setNamedColor(color)

    _format = QTextCharFormat()
    _format.setForeground(_color)
    if "bold" in style:
        _format.setFontWeight(QFont.Bold)
    if "italic" in style:
        _format.setFontItalic(True)

    return _format


# Syntax styles that can be shared by all languages
STYLES = {
    "keyword": format("#BE54FF"),
    "operator": format("#DDDDDD"),
    "brace": format("#DDDDDD"),
    "defclass": format("#FFDB3B", "bold"),
    "string": format("#D18767"),
    "string2": format("#D18767"),
    "comment": format("#36B500"),
    "self": format("#66D1FF"),
    "numbers": format("#DDDDDD"),
    "mc": format("#FF00EA", "bold"),
}


# TODO - complete this! This is currently only an example that can highlight "def" statements, but should be able to fully make it a Python syntax highlighter
class PythonHighlighter(QSyntaxHighlighter):
    # Python keywords
    keywords = [
        "and",
        "assert",
        "break",
        "class",
        "continue",
        "def",
        "del",
        "elif",
        "else",
        "except",
        "exec",
        "finally",
        "for",
        "from",
        "global",
        "if",
        "import",
        "in",
        "is",
        "lambda",
        "not",
        "or",
        "pass",
        "print",
        "raise",
        "return",
        "try",
        "while",
        "yield",
        "None",
        "True",
        "False",
    ]

    # Python operators
    operators = [
        "=",
        # Comparison
        "==",
        "!=",
        "<",
        "<=",
        ">",
        ">=",
        # Arithmetic
        "\\+",
        "-",
        "\\*",
        "/",
        "//",
        "\\%",
        "\\*\\*",
        # In-place
        "\\+=",
        "-=",
        "\\*=",
        "/=",
        "\\%=",
        # Bitwise
        "\\^",
        "\\|",
        "\\&",
        "\\~",
        ">>",
        "<<",
    ]

    # Python braces
    braces = [
        "\\{",
        "\\}",
        "\\(",
        "\\)",
        "\\[",
        "\\]",
    ]

    def __init__(self, parent: QTextDocument) -> None:
        QSyntaxHighlighter.__init__(self, parent)

        # Multi-line strings (expression, flag, style)
        self.tri_single = (QRegularExpression("'''"), 1, STYLES["string2"])
        self.tri_double = (QRegularExpression('"""'), 2, STYLES["string2"])

        rules = []

        # Keyword, operator, and brace rules
        rules += [
            (r"\b%s\b" % w, 0, STYLES["keyword"]) for w in PythonHighlighter.keywords
        ]
        rules += [
            (r"%s" % o, 0, STYLES["operator"]) for o in PythonHighlighter.operators
        ]
        rules += [(r"%s" % b, 0, STYLES["brace"]) for b in PythonHighlighter.braces]

        # All other rules
        rules += [
            # 'self'
            (r"\bself\b", 0, STYLES["self"]),
            # 'def' followed by an identifier
            (r"\bdef\b\s*(\w+)", 1, STYLES["defclass"]),
            # 'class' followed by an identifier
            (r"\bclass\b\s*(\w+)", 1, STYLES["defclass"]),
            # Numeric literals
            (r"\b[+-]?[0-9]+[lL]?\b", 0, STYLES["numbers"]),
            (r"\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b", 0, STYLES["numbers"]),
            (r"\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b", 0, STYLES["numbers"]),
            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES["string"]),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES["string"]),
            # From '#' until a newline
            (r"#[^\n]*", 0, STYLES["comment"]),
            # mc(...)(...) - monte carlo identifier, opener and closer
            (r"(mc\([\d\.]+\))((\()((?>[^\(\)]+|(?2))*(\))))", 1, STYLES["mc"]),
            (r"(mc\([\d\.]+\))((\()((?>[^\(\)]+|(?2))*(\))))", 3, STYLES["mc"]),
            (r"(mc\([\d\.]+\))((\()((?>[^\(\)]+|(?2))*(\))))", 5, STYLES["mc"]),
        ]

        # Build a QRegularExpression for each pattern
        self.rules = [
            (QRegularExpression(pat), index, fmt) for (pat, index, fmt) in rules
        ]

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text."""
        self.tripleQuoutesWithinStrings = []
        # Do other syntax formatting
        for expression, nth, format in self.rules:
            matchobj = expression.match(text, 0)
            index = matchobj.capturedStart()
            if index >= 0:
                # if there is a string we check
                # if there are some triple quotes within the string
                # they will be ignored if they are matched again
                if expression.pattern() in [
                    r'"[^"\\]*(\\.[^"\\]*)*"',
                    r"'[^'\\]*(\\.[^'\\]*)*'",
                ]:
                    innerIndex = (
                        self.tri_single[0].match(text, index + 1).capturedStart()
                    )
                    if innerIndex == -1:
                        innerIndex = (
                            self.tri_double[0].match(text, index + 1).capturedStart()
                        )

                    if innerIndex != -1:
                        tripleQuoteIndexes = range(innerIndex, innerIndex + 3)
                        self.tripleQuoutesWithinStrings.extend(tripleQuoteIndexes)

            while index >= 0:
                # skipping triple quotes within strings
                if index in self.tripleQuoutesWithinStrings:
                    index += 1
                    expression.match(text, index)
                    continue

                # We actually want the index of the nth match
                index = matchobj.capturedStart(nth)
                length = len(matchobj.captured(nth))
                self.setFormat(index, length, format)
                matchobj = expression.match(text, index + length)
                index = matchobj.capturedStart()

        self.setCurrentBlockState(0)

        # Do multi-line strings
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.tri_double)

    def match_multiline(self, text, delimiter, in_state, style):
        """Do highlighting of multi-line strings. ``delimiter`` should be a
        ``QRegExp`` for triple-single-quotes or triple-double-quotes, and
        ``in_state`` should be a unique integer to represent the corresponding
        state changes when inside those strings. Returns True if we're still
        inside a multi-line string when this function is finished.
        """
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            startmatch = delimiter.match(text)
            start = startmatch.capturedStart()
            # skipping triple quotes within strings
            if start in self.tripleQuoutesWithinStrings:
                return False
            # Move past this match
            add = startmatch.capturedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            endmatch = delimiter.match(text, start + add)
            end = endmatch.capturedStart()
            # Ending delimiter on this line?
            if end >= add:
                length = end - start + add + endmatch.capturedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            # Apply formatting
            self.setFormat(start, length, style)
            # Look for the next match
            startmatch = delimiter.match(text, start + length)
            start = startmatch.capturedStart()

        # Return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == in_state:
            return True
        else:
            return False
