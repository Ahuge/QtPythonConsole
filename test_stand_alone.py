
import sys
sys.path.append('C:/Users/pgerrish/MyScripts')




if __name__ == '__main__':
    from PySide import QtGui
    app = QtGui.QApplication(sys.argv)
    import QtPythonConsole.console as csl
    console = csl.ConsoleDialog()
    console.show()
    sys.exit(app.exec_())