from Qt import QtWidgets

from widgets.output import OutputConsole
from widgets.input import InputConsole
import code


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
        self.setWindowTitle("Rv Python Console")
        self.top_layout.setSpacing(0)
        self.top_layout.setContentsMargins(0, 0, 0, 0)


class ConsoleWidget(QtWidgets.QWidget):
    def __init__(self, _locals=None, *args, **kwargs):
        super(ConsoleWidget, self).__init__(*args, **kwargs)
        if _locals is None:
            _locals = {}

        # create widgets
        self.clear_button = QtWidgets.QPushButton("Clear")
        self.output_console = OutputConsole()
        self.locals = _locals
        self.input_console = InputConsole(
            appname="Rv Python Terminal",
            stdout=self.output_console.stdin,
            parent=self,
        )

        # create layouts
        self.top_layout = QtWidgets.QVBoxLayout(self)

        # connect layouts
        self.top_layout.addWidget(self.input_console)
        self.top_layout.addWidget(self.output_console)
        self.top_layout.addWidget(self.clear_button)

        # set properties
        self.setContentsMargins(0, 0, 0, 0)

        # connect signals
        self.input_console.CODE_EXECUTED.connect(self.output_console.read_stdin)
        self.clear_button.clicked.connect(self.output_console.clear)


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
