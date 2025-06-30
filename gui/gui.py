import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from Ui_test import Ui_MainWindow



class mywindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(mywindow,self).__init__()
        self.setupUi(self)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = mywindow()
    window.show()
    sys.exit(app.exec_())
