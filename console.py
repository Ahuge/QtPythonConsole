import os

from Qt import QtWidgets, QtGui, QtCore

from widgets.output import OutputConsole
from widgets.input import InputConsole


class ConsoleDialog(QtWidgets.QDialog):
    def __init__(self, _locals=None, *args, **kwargs):
        super(ConsoleDialog, self).__init__(*args, **kwargs)

        # create widgets
        self.console_widget = ConsoleWidget(parent=self, _locals=_locals)

        # create layouts
        self.top_layout = QtWidgets.QVBoxLayout(self)

        # connect layouts
        self.top_layout.addWidget(self.console_widget)

        # set properties
        self.setWindowTitle("Python Console")
        self.top_layout.setSpacing(0)
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.setMinimumSize(1200, 800)


class ConsoleWidget(QtWidgets.QWidget):
    def __init__(self, _locals=None, *args, **kwargs):
        super(ConsoleWidget, self).__init__(*args, **kwargs)
        self.decorate_application()

        if _locals is None:
            _locals = {}

        # create widgets
        self.clear_button = QtWidgets.QPushButton("Clear")
        self.output_console = OutputConsole()
        self.locals = _locals
        self.input_console = InputConsole(
            appname="Python Terminal",
            stdout=self.output_console.stdin,
            parent=self,
        )

        # create layouts
        self.top_layout = QtWidgets.QVBoxLayout(self)

        self.splitter = QtWidgets.QSplitter()
        self.splitter.addWidget(self.input_console)
        self.splitter.addWidget(self.output_console)

        self.button_box = QtWidgets.QWidget()
        self.button_box.setSizePolicy(self.button_box.sizePolicy().horizontalPolicy(), QtWidgets.QSizePolicy.Fixed)
        self.button_box.setLayout(QtWidgets.QHBoxLayout())
        self.button_box.layout().addStretch(1)
        self.button_box.layout().addWidget(self.clear_button)

        self.top_layout.addWidget(self.splitter)
        self.top_layout.addWidget(self.button_box)

        # set properties
        self.setContentsMargins(0, 0, 0, 0)
        self.button_box.setContentsMargins(0, 0, 0, 0)
        self.button_box.layout().setContentsMargins(0, 0, 0, 0)
        self.button_box.layout().setSpacing(0)

        # connect signals
        self.input_console.CODE_EXECUTED.connect(self.output_console.read_stdin)
        self.input_console.clear_output.connect(self.output_console.clear)
        self.clear_button.clicked.connect(self.output_console.clear)

        # self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # self.customContextMenuRequested.connect()

    def decorate_application(self):
        palette_path = os.path.join(os.path.dirname(__file__), "dark_palette.qpalette")
        fh = QtCore.QFile(palette_path)
        fh.open(QtCore.QIODevice.ReadOnly)
        file_in = QtCore.QDataStream(fh)
        dark_palette = QtGui.QPalette()
        file_in.__rshift__(dark_palette)
        fh.close()

        highlight_color = QtGui.QBrush(QtGui.QColor("#18A7E3"))
        dark_palette.setBrush(QtGui.QPalette.Highlight, highlight_color)

        # update link colors
        fg_color = dark_palette.color(QtGui.QPalette.Text)
        dark_palette.setColor(QtGui.QPalette.Link, fg_color)
        dark_palette.setColor(QtGui.QPalette.LinkVisited, fg_color)

        dark_palette.setBrush(QtGui.QPalette.HighlightedText, QtGui.QBrush(QtGui.QColor("#FFFFFF")))

        bgc = QtGui.QColor(35, 35, 35)
        dark_palette.setColor(QtGui.QPalette.Base, bgc)

        bgc = QtGui.QColor(60, 60, 60)
        dark_palette.setColor(QtGui.QPalette.Button, bgc)

        bgc = QtGui.QColor(65, 65, 65)
        dark_palette.setColor(QtGui.QPalette.Window, bgc)

        # and associate it with the qapplication
        QtWidgets.QApplication.setPalette(dark_palette)

    def createStandardContextMenu(self):
        menu = QtWidgets.QMenu("ContextMenu")
        menu.addSeparator()
        menu.addAction("Rotate...", self.rotate_splitter)
        return menu

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        menu.exec_(self.mapToGlobal(event.pos()))

    @QtCore.Slot()
    def rotate_splitter(self):
        if self.splitter.orientation() == QtCore.Qt.Horizontal:
            self.splitter.setOrientation(QtCore.Qt.Vertical)
        else:
            self.splitter.setOrientation(QtCore.Qt.Horizontal)

    def keyPressEvent(self, e):
        # Enter or return pressed with control modifier
        if e.modifiers() == QtCore.Qt.ControlModifier and e.key() == QtCore.Qt.Key_R:
            self.rotate_splitter()
            e.accept()
            return
        elif e.modifiers() & QtCore.Qt.ControlModifier and e.modifiers() & QtCore.Qt.ShiftModifier and e.key() == QtCore.Qt.Key_C:
            self.clear_console()
            e.accept()
            return

    @QtCore.Slot()
    def clear_console(self):
        self.output_console.clear()


if __name__ == "__main__":
    from Qt import QtWidgets
    app = QtWidgets.QApplication.instance()
    created = False
    if not app:
        app = QtWidgets.QApplication([])
        created = True
    d = ConsoleDialog()
    d.show()
    if created:
        app.exec_()
