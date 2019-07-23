from six.moves import cStringIO as StringIO

from Qt import QtGui
from .textedit import TextEdit


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
        value = self.stdin.getvalue()
        value = value.replace("\0", "")
        self.document().setPlainText(value)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def clear(self):
        self.stdin.truncate(0)
        self.document().setPlainText("")

    def createStandardContextMenu(self):
        menu = super(TextEdit, self).createStandardContextMenu()
        menu.addSeparator()
        menu.addAction("Clear...", self.clear)
        return menu

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        menu.exec_(self.mapToGlobal(event.pos()))
