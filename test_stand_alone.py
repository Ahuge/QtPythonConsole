import sys


def test_cmdline(argv):
    from Qt import QtGui
    app = QtGui.QApplication(argv)
    import console as csl
    console = csl.ConsoleDialog()
    console.show()
    sys.exit(app.exec_())


def test_widget():
    from Qt import QtGui, QtCore
    from console import ConsoleWidget
    app = QtGui.QApplication.instance()
    if not app:
        app = QtGui.QApplication([])

    window = QtGui.QMainWindow()
    dialog = QtGui.QDockWidget()
    dialog.setTitleBarWidget(QtGui.QLabel("Python Terminal"))
    widget = ConsoleWidget()
    dialog.setWidget(widget)
    window.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dialog)
    # d = ConsoleDialog()
    # d.show()
    window.show()
    app.exec_()


if __name__ == '__main__':
    if sys.argv[-1] == "dock":
        test_widget()
    else:
        test_cmdline(sys.argv)
