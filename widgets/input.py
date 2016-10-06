import sys
import json
from Qt import QtCore, QtGui, QtWidgets
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

        self.set_completer(Completer(QtGui.QAbstractListModel(['One Fish', 'Two Fish', 'Red Fish', 'Salamander!'])))
        self.user = User(appname)
        self.interpreter = interpreter
        self.s = stdout
        if code is None:
            self.loadUserCache()
            self.textChanged.connect(self.saveUserCache)
        else:
            self.document().setPlainText(code)

        self.highlighter = MyHighlighter(self.document())
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        # Temporary setting to execute raw text untill sysout is stable
        self.DEBUG_STRING_EXECUTE = True

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

    def set_completer(self, completer):
        if self.completer:
            self.disconnect(self.completer, 0, 0)
        self.completer = completer
        if self.completer:
            self.completer.setWidget(self)
            self.completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
            self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
            self.completer.activated.connect(self.insert_completion)

    def completer(self):
        return self.completer

    def insert_completion(self, string):
        print string, '----->>>'
        tc = self.textCursor()
        tc.movePosition(QtGui.QTextCursor.StartOfWord, QtGui.QTextCursor.KeepAnchor)
        tc.insertText(string)
        self.setTextCursor(tc)

    def textUnderCursor(self):
        tc = self.textCursor()
        tc.select(QtGui.QTextCursor.WordUnderCursor)
        return tc.selectedText()

    def keyPressEvent(self, e):

        # Make sure to add descriptiveQAbstractListModel comments for any new keyPress events...
        completer_model = self.completer.model()
        completer_model.items = ['Potatoes', 'barley']
        self.completer.popup().show()
        self.completer.popup().setCurrentIndex(completer_model.index(0, 0))

        curser_rect = self.cursorRect()
        curser_rect.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(curser_rect)

        # Handle Ctrl+Enter event
        if e.modifiers() == QtCore.Qt.ControlModifier and (
                        e.key() == QtCore.Qt.Key_Enter or e.key() == QtCore.Qt.Key_Return):
            if self.DEBUG_STRING_EXECUTE:
                exec(self.toPlainText())
                return
            else:
                self.executeSelected()
            return

        # Handle Tab event
        elif e.key() == QtCore.Qt.Key_Tab:
            tc = self.textCursor()
            tc.insertText('   ')
            self.setTextCursor(tc)
            return






        # Fall back to default functionality
        else:
            super(InputConsole, self).keyPressEvent(e)
