import sys
import json
from Qt.Qt import QtCore, QtGui, QtWidgets
from QtPythonConsole.user import User
from utils import Completer, MyHighlighter
from textedit import TextEdit

DEFAULT_CODE = '#use the variable "projects" to refer to currently selected items in the project tree'


class InputConsole(TextEdit):
    code = QtCore.Signal(str)
    CODE_EXECUTED = QtCore.Signal()

    def __init__(self, parent=None, code=None, appname=None, stdout=None, interpreter=None):
        super(InputConsole, self).__init__(parent)
        self.completer = None
        self.namespace = globals().copy()
        self.setCompleter(Completer([]))
        self.user = User(appname)
        self.interpreter = interpreter
        self.stdout = stdout
        if code is None:
            self.loadUserCache()
            self.textChanged.connect(self.saveUserCache)
        else:
            self.document().setPlainText(code)

        self.highlighter = MyHighlighter(self.document())
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

    def emitCode(self):
        self.code.emit(self.toPlainText())

    def redirect_stdout(self):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = self.stdout
            sys.stderr = self.stdout
            yield self.stdout
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            self.CODE_EXECUTED.emit()
            self.user.save(self.toPlainText(), "wb")

    def executeContents(self):
        for pipe in self.redirect_stdout():
            result = "default"
            for line in self.toPlainText().split("\n"):
                if result is True:
                    # We are expecting more input.
                    if not line.startswith(" "):
                        # We are going to attempt to add a newline in there.
                        self.interpreter.push("")
                result = self.interpreter.push(line)

    def executeSelected(self):
        selected_text = "\n".join(self.textCursor().selectedText().splitlines())
        if selected_text:
            for pipe in self.redirect_stdout():
                result = "default"
                for line in selected_text.split("\n"):
                    if result is True:
                        # We are expecting more input.
                        if not line.startswith(" "):
                            # We are going to attempt to add a newline in there.
                            self.interpreter.push("")
                    result = self.interpreter.push(line)
        else:
            self.executeContents()

    @staticmethod
    def mimeTypes():
        return ['text/plain', 'text/uri-list', 'text/python-code']

    def canInsertFromMimeData(self, mimedata):
        for text_format in ['text/plain', 'text/uri-list', 'text/python-code']:
            if mimedata.hasFormat(text_format):
                return True
        return super(InputConsole, self).canInsertFromMimeData(mimedata)

    def dragMoveEvent(self, event):
        mimeData = event.mimeData()
        mimeData.setData('text/python-code', mimeData.data('text/plain'))
        super(InputConsole, self).dragMoveEvent(event)

    def insertFromMimeData(self, mimeData):
        if mimeData.hasFormat('text/uri-list'):
            urls = mimeData.urls()
            firstPath = str(urls[0].path())[1:]
            if firstPath.endswith('.py'):
                with open(firstPath, mode='r') as f:
                    self.document().setPlainText(f.read())
                    return True
            if firstPath.endswith('.json'):
                with open(firstPath, mode='r') as f:
                    data = json.loads(f.read())
                    if 'code' in data:
                        self.document().setPlainText(data['code'])
                    return True
        super(InputConsole, self).insertFromMimeData(mimeData)

    def highlightCurrentLine(self):
        # Create a selection region that shows the current line
        # Taken from the codeeditor.cpp exampl(
        selection = QtWidgets.QTextEdit.ExtraSelection()
        lineColor = QtGui.QColor(44, 33, 44)

        selection.format.setBackground(lineColor)
        selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        self.setExtraSelections([selection])

    def loadUserCache(self):
        userCode = self.user.read()
        if userCode:
            self.document().setPlainText(userCode)
        else:
            self.document().setPlainText(DEFAULT_CODE)

    def saveUserCache(self):
        self.user.save(self.document().toPlainText(), "wb")

    def createStandardContextMenu(self):
        menu = super(TextEdit, self).createStandardContextMenu()
        menu.addAction("Execute Code", self.executeContents)
        menu.addAction("Execute Selected", self.executeSelected)
        return menu

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        menu.exec_(self.mapToGlobal(event.pos()))

    def setCompleter(self, completer):
        if self.completer:
            self.disconnect(self.completer, 0, 0)
        self.completer = completer
        if not self.completer:
            return
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.completer.activated.connect(self.insertCompletion)
        # self.connect(self.completer, SIGNAL('activated(QString)'), self.insertCompletion)

    def completer(self):
        return self.completer

    def insertCompletion(self, string):
        tc = self.textCursor()
        tc.movePosition(QtGui.QTextCursor.StartOfWord, QtGui.QTextCursor.KeepAnchor)
        tc.insertText(string)
        self.setTextCursor(tc)

    def textUnderCursor(self):
        tc = self.textCursor()
        tc.select(QtGui.QTextCursor.WordUnderCursor)
        return tc.selectedText()

    def keyPressEvent(self, e):

        # Enter or return pressed with control modifier
        if e.modifiers() == QtCore.Qt.ControlModifier and (
                        e.key() == QtCore.Qt.Key_Enter or e.key() == QtCore.Qt.Key_Return):
            self.executeSelected()
            return

        if e.key() == QtCore.Qt.Key_Tab:
            tc = self.textCursor()
            tc.insertText('   ')
            self.setTextCursor(tc)
            return

        # Completer in progress
        if self.completer and self.completer.popup().isVisible():
            if e.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return, QtCore.Qt.Key_Escape,
                           QtCore.Qt.Key_Tab, QtCore.Qt.Key_Backtab):
                e.ignore()
                return

        isShortcut = ((e.modifiers() & QtCore.Qt.ControlModifier) and e.key() == QtCore.Qt.Key_E)
        if not self.completer or not isShortcut:
            return super(TextEdit, self).keyPressEvent(e)

        ctrlOrShift = e.modifiers() & (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier)
        if not self.completer or (ctrlOrShift and not e.text()):
            return

        eow = str("~!@#$%^&*()_+{}|:\"<>?,./;'[]\\-=")
        hasModifier = (e.modifiers() != QtCore.Qt.NoModifier) and not ctrlOrShift
        completionPrefix = self.textUnderCursor()

        if (not isShortcut
            and (hasModifier
                 or not e.text()
                 or len(completionPrefix) < 2
                 or e.text()[-1] in eow)):
            self.completer.popup().hide()
            return

        itemList = self.namespace.keys()
        self.completer.update([k for k in itemList if completionPrefix in k])
        self.completer.popup().setCurrentIndex(self.completer.completionModel().index(0, 0))

        cr = self.cursorRect()
        cr.setWidth(self.completer.popup().sizeHintForColumn(0)
                    + self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(cr)

    def setCode(self, code):
        self.document().setPlainText(code)
