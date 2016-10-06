try:
    from PySide import QtCore, QtGui
    # pyside 1 doesnt have QtWidgets
    QtWidgets = QtGui

except ImportError:
    # Assumes PySide2
    from PySide2 import QtCore, QtWidgets, QtGui
