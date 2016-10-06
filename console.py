from Qt.Qt import QtWidgets

from widgets.output import OutputConsole
from widgets.input import InputConsole
import code


class ConsoleDialog(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        super(ConsoleDialog, self).__init__(*args, **kwargs)

        # create widgets
        self.console_widget = ConsoleWidget(self)

        # create layouts
        self.top_layout = QtWidgets.QVBoxLayout(self)

        # connect layouts
        self.top_layout.addWidget(self.console_widget)

        # set properties
        self.setWindowTitle("Rv Python Console")
        self.top_layout.setSpacing(0)
        self.top_layout.setContentsMargins(0, 0, 0, 0)


class ConsoleWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(ConsoleWidget, self).__init__(*args, **kwargs)

        # create widgets
        self.clear_button = QtWidgets.QPushButton("Clear")
        self.output_console = OutputConsole()
        self.input_console = InputConsole(
            appname="Rv Python Terminal",
            interpreter=code.InteractiveConsole(),
            stdout=self.output_console.stdin
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
    from Qt import QtGui
    app = QtGui.QApplication.instance()
    if not app:
        app = QtGui.QApplication([])
    d = ConsoleDialog()
    d.show()
    app.exec_()
