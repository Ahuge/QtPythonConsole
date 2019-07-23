import contextlib
import sys
import json
import re

from Qt import QtCore, QtGui, QtWidgets
import six

from six import text_type

from QtPythonConsole.user import User
from .utils import Completer, MyHighlighter
from .textedit import TextEdit

DEFAULT_CODE = '#use the variable "projects" to refer to currently selected items in the project tree'


class InputConsole(TextEdit):
    code = QtCore.Signal(str)
    CODE_EXECUTED = QtCore.Signal()
    LINE_CONST = "LINENUMBERCONST"
    EXCEPTION_MESSAGE = """
RuntimeError: The following exception was thrown while executing code from line {start_row}-{end_row}:
    {exception}"""

    def __init__(self, parent=None, code=None, appname=None, stdout=None):
        super(InputConsole, self).__init__(parent)
        self.completer = None
        self.namespace = globals().copy()
        self.setCompleter(Completer([]))
        self.user = User(appname)
        self.stdout = stdout
        if code is None:
            self.loadUserCache()
            self.textChanged.connect(self.saveUserCache)
        else:
            self.document().setPlainText(code)

        self.highlighter = MyHighlighter(self.document())
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.locals_added = self.parent().locals
        self.locals_removed = {}

    def emitCode(self):
        self.code.emit(self.toPlainText())

    @contextlib.contextmanager
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
            self.user.save(self.toPlainText(), "w")

    @contextlib.contextmanager
    def patch_globals(self):
        backup = globals().copy()
        backup_keys = set(backup.keys())
        try:
            for key in self.locals_added:
                globals()[key] = self.locals_added[key]
            for key in self.locals_removed:
                del globals()[key]
            yield

        finally:
            added = {}
            removed = {}
            new_keys = set(globals().keys())
            difference = set({}).union(
                backup_keys.difference(new_keys),
                new_keys.difference(backup_keys)
            )
            intersection = backup_keys.intersection(new_keys)

            for key in intersection:
                if backup[key] != globals()[key]:
                    added[key] = globals()[key]
            for key in difference:
                if key in backup:
                    # Removed
                    removed[key] = backup[key]
                elif key in self.locals_added:
                    del self.locals_added[key]
                elif key in globals():
                    # Added
                    added[key] = globals()[key]
            self.locals_added = added
            self.locals_removed = removed
            for key in self.locals_added:
                del globals()[key]
            globals().update(backup)

    def executeContents(self):
        self.executeCode(self.toPlainText())

    def executeSelected(self):
        lines = self.textCursor().selectedText().splitlines()
        selected_text = "\n".join(lines)
        if selected_text:
            try:
                self.executeCode(selected_text)
            except BaseException as err:
                row = self.textCursor().blockNumber()
                with self.redirect_stdout():
                    import traceback
                    message = traceback.format_exception_only(type(err), err)
                    error = self.EXCEPTION_MESSAGE.format(
                        exception="\n".join(message),
                        start_row=row+1,
                        end_row=row+len(lines)
                    )
                    print(error)
        else:
            self.executeContents()

    def executeCode(self, code):
        if "del " in code:
            code = re.sub(r"(\s*)del\s([^;\n]+)", r"\1if '\2' in locals():\n\1    del \2\n\1else:\n\1    del globals()['\2']", code)
        with self.redirect_stdout():
            with self.patch_globals():
                result = ""
                ___locals = locals().copy()
                try:
                    result = eval(code, globals(), globals())
                except SyntaxError:
                    if six.PY3:
                        six.exec_(code)
                    else:
                        six.exec_(code, globals=globals(), locals=globals())
                except BaseException:
                    raise

                for key in set(locals().keys()).difference(set(___locals.keys())):
                    if key != "_%s___locals" % self.__class__.__name__:
                        globals()[key] = locals()[key]

                if result:
                    print(result)

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
            self.document().setPlainText(text_type(userCode))
        else:
            self.document().setPlainText(DEFAULT_CODE)

    def saveUserCache(self):
        self.user.save(self.document().toPlainText(), "w")

    def createStandardContextMenu(self):
        menu = super(TextEdit, self).createStandardContextMenu()
        menu.addSeparator()
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
