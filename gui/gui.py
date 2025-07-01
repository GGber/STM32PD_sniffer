import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from Ui_test import Ui_MainWindow
from myusb import USBDeviceManager


class mywindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(mywindow,self).__init__()
        self.setupUi(self)

        self.setWindowTitle("USB Device Manager")
        self.setGeometry(100, 100, 800, 600)

        # 初始化 USB 设备管理器
        self.usb_manager = USBDeviceManager()

        # 获取设备信息
        devices = self.usb_manager.list_devices()

        # 清空并添加到 comboBox_usb 控件中
        self.comboBox_usb.clear()
        self.comboBox_usb.addItems(devices)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = mywindow()
    window.show()
    sys.exit(app.exec_())
