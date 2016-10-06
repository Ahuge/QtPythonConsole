from Qt.Qt import QtGui, QtWidgets


class TextEdit(QtWidgets.QTextEdit):
    def __init__(self, parent=None):
        super(TextEdit, self).__init__(parent)
        font = QtGui.QFont('courier', 11, True)
        self.setFont(font)
        self.wrap = False

    @property
    def wrap(self):
        option = self.document().defaultTextOption()
        return not bool(option.wrapMode() == option.NoWrap)

    @wrap.setter
    def wrap(self, value):
        option = self.document().defaultTextOption()
        if value:
            option.setWrapMode(option.WrapAtWordBoundaryOrAnywhere)
        else:
            option.setWrapMode(option.NoWrap)
        self.document().setDefaultTextOption(option)
