from cStringIO import StringIO
from Qt.Qt import QtGui
from textedit import TextEdit


class OutputConsole(TextEdit):
    def __init__(self, parent=None):
        super(OutputConsole, self).__init__(parent)
        self.stdin = StringIO()
        self.setReadOnly(True)
        font = QtGui.QFont('courier', 9)
        self.setFont(font)
        pal = QtGui.QPalette()
        bgc = QtGui.QColor(50, 50, 50)
        pal.setColor(QtGui.QPalette.Base, bgc)
        text_color = QtGui.QColor(175, 175, 175)
        pal.setColor(QtGui.QPalette.Text, text_color)
        self.setPalette(pal)

    def read_stdin(self):
        self.document().setPlainText(self.stdin.getvalue())

    def clear(self):
        self.stdin.truncate(0)
        self.document().setPlainText("")
