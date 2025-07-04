import sys
import threading
import time
import logging
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import (
    QApplication, QLabel, QTextEdit, QPushButton,
    QVBoxLayout, QLineEdit, QComboBox, QWidget,
    QHBoxLayout, QGroupBox, QSplitter, QGridLayout,
    QMessageBox
)
from PyQt5.QtCore import QTimer, pyqtSignal, Qt
from myusb import USBDeviceManager
from Ui_test import Ui_MainWindow

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('usb_app.log')
    ]
)
logger = logging.getLogger(__name__)

class MyWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    data_received = pyqtSignal(int, bytes)  # 接口索引, 数据
    connection_status_changed = pyqtSignal(bool)  # 连接状态改变信号

    def __init__(self):
        super(MyWindow, self).__init__()
        self.setupUi(self)
        
        self.setWindowTitle("Dual WINUSB GUI")
        self.resize(800, 600)  # 更合理的默认窗口大小
        
        # USB设备管理
        self.usb = USBDeviceManager(vid=0x1514, pid=0x1000)
        self.interface_count = 2
        self.device_connected = False
        self.running = True  # 控制线程运行的标志
        
        # 创建UI组件
        self.setup_ui()
        
        # 连接信号和槽
        self.connect_signals()
        
        # 启动定时器和线程
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_device)
        self.timer.start(1000)  # 每秒检查一次设备
        
        # 启动读取线程
        self.reader_thread = threading.Thread(target=self.read_loop, daemon=True)
        self.reader_thread.start()
    
    def setup_ui(self):
        """设置用户界面"""
        # 主布局
        main_layout = QVBoxLayout()
        
        # 状态和控制区域
        status_group = QGroupBox("设备状态")
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("断开连接")
        self.status_label.setStyleSheet("background-color: red; padding: 5px; border-radius: 5px;")
        status_layout.addWidget(self.status_label)
        
        self.connect_button = QPushButton("连接")
        self.connect_button.clicked.connect(self.toggle_connection)
        status_layout.addWidget(self.connect_button)
        
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        # 接口选择和数据发送区域
        send_group = QGroupBox("发送数据")
        send_layout = QGridLayout()
        
        send_layout.addWidget(QLabel("接口:"), 0, 0)
        self.interface_combo = QComboBox()
        self.interface_combo.addItems([f"接口 {i}" for i in range(self.interface_count)])
        send_layout.addWidget(self.interface_combo, 0, 1)
        
        send_layout.addWidget(QLabel("数据:"), 1, 0)
        self.send_input = QLineEdit()
        self.send_input.setPlaceholderText("输入要发送的数据")
        send_layout.addWidget(self.send_input, 1, 1)
        
        self.send_hex_checkbox = QComboBox()
        self.send_hex_checkbox.addItems(["ASCII", "HEX"])
        send_layout.addWidget(self.send_hex_checkbox, 1, 2)
        
        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self.send_data)
        send_layout.addWidget(self.send_button, 1, 3)
        
        send_group.setLayout(send_layout)
        main_layout.addWidget(send_group)
        
        # 接收数据区域
        recv_group = QGroupBox("接收数据")
        recv_layout = QVBoxLayout()
        
        self.clear_button = QPushButton("清空接收区")
        self.clear_button.clicked.connect(self.clear_received_data)
        recv_layout.addWidget(self.clear_button)
        
        self.recv_text = QTextEdit()
        self.recv_text.setReadOnly(True)
        self.recv_text.setLineWrapMode(QTextEdit.NoWrap)
        recv_layout.addWidget(self.recv_text)
        
        recv_group.setLayout(recv_layout)
        main_layout.addWidget(recv_group, 1)  # 给接收区更多的垂直空间
        
        # 设置主窗口布局
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
    
    def connect_signals(self):
        """连接信号和槽"""
        self.data_received.connect(self.update_received_data)
        self.connection_status_changed.connect(self.update_connection_status)
    
    def toggle_connection(self):
        """切换设备连接状态"""
        if self.device_connected:
            try:
                self.usb.disconnect()
                self.device_connected = False
                self.connection_status_changed.emit(False)
                logger.info("设备已断开连接")
            except Exception as e:
                logger.error(f"断开连接失败: {e}")
                QMessageBox.warning(self, "错误", f"断开连接失败: {e}")
        else:
            self.check_device(force_connect=True)
    
    def check_device(self, force_connect=False):
        """
        检查设备连接状态
        :param force_connect: 是否强制尝试连接
        """
        if self.device_connected and not force_connect:
            return  # 如果已连接且不是强制连接，则直接返回
        
        try:
            self.usb.connect()
            if not self.device_connected:
                self.device_connected = True
                self.connection_status_changed.emit(True)
                logger.info("设备已连接")
        except Exception as e:
            if force_connect:
                logger.error(f"设备连接失败: {e}")
                QMessageBox.warning(self, "错误", f"设备连接失败: {e}")
            elif self.device_connected:
                self.device_connected = False
                self.connection_status_changed.emit(False)
                logger.info("设备已断开连接")
            else:
                logger.debug(f"设备未连接: {e}")
    
    def update_connection_status(self, connected):
        """更新连接状态UI"""
        if connected:
            self.status_label.setText("已连接")
            self.status_label.setStyleSheet("background-color: green; color: white; padding: 5px; border-radius: 5px;")
            self.connect_button.setText("断开连接")
        else:
            self.status_label.setText("断开连接")
            self.status_label.setStyleSheet("background-color: red; color: white; padding: 5px; border-radius: 5px;")
            self.connect_button.setText("连接")
    
    def send_data(self):
        """发送数据到设备"""
        if not self.device_connected:
            QMessageBox.warning(self, "警告", "设备未连接，无法发送数据")
            return
        
        text = self.send_input.text()
        if not text:
            return
        
        # 根据选择的模式转换数据
        if self.send_hex_checkbox.currentText() == "HEX":
            try:
                # 移除所有空格，确保格式正确
                hex_string = text.replace(" ", "")
                # 检查长度是否为偶数
                if len(hex_string) % 2 != 0:
                    raise ValueError("HEX字符串长度必须为偶数")
                data = bytes.fromhex(hex_string)
            except Exception as e:
                QMessageBox.warning(self, "错误", f"HEX格式错误: {e}")
                return
        else:
            data = text.encode()
        
        intf = self.interface_combo.currentIndex()
        try:
            self.usb.send(data, interface_index=intf)
            logger.info(f"数据已发送到接口 {intf}: {data}")
            
            # 在接收区显示发送的数据
            self.recv_text.append(f"[发送到接口 {intf}] {self.format_data(data)}")
        except Exception as e:
            logger.error(f"发送失败: {e}")
            QMessageBox.warning(self, "错误", f"发送失败: {e}")
    
    def format_data(self, data):
        """格式化数据以便显示"""
        if self.send_hex_checkbox.currentText() == "HEX":
            return ' '.join(f"{b:02X}" for b in data)
        else:
            return data.decode(errors='replace')
    
    def read_loop(self):
        """后台读取线程"""
        while self.running:
            if self.device_connected:
                for i in range(self.interface_count):
                    try:
                        data = self.usb.receive(interface_index=i)
                        if data and len(data) > 0:
                            self.data_received.emit(i, data)
                    except Exception as e:
                        if "Pipe error" not in str(e):  # 忽略常见的管道错误
                            logger.debug(f"从接口 {i} 读取数据时出错: {e}")
            time.sleep(0.01)  # 短暂休眠以减少CPU使用率
    
    def update_received_data(self, interface_index, data):
        """更新接收到的数据到UI"""
        try:
            # 创建格式化的输出
            formatted_data = self.format_data(data)
            text = f"[接收自接口 {interface_index}] {formatted_data}"
            
            # 如果接收区文本太长，可以自动删除旧内容
            if self.recv_text.document().blockCount() > 1000:
                cursor = self.recv_text.textCursor()
                cursor.movePosition(QtCore.QTextCursor.Start)
                cursor.movePosition(QtCore.QTextCursor.Down, QtCore.QTextCursor.KeepAnchor, 100)
                cursor.removeSelectedText()
                
            self.recv_text.append(text)
            # 滚动到底部
            self.recv_text.verticalScrollBar().setValue(
                self.recv_text.verticalScrollBar().maximum()
            )
        except Exception as e:
            logger.error(f"更新接收数据到UI失败: {e}")
    
    def clear_received_data(self):
        """清空接收文本框"""
        self.recv_text.clear()
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        self.running = False  # 停止读取线程
        
        # 确保断开USB连接
        if self.device_connected:
            try:
                self.usb.disconnect()
                logger.info("关闭窗口时断开USB连接")
            except Exception as e:
                logger.error(f"断开连接失败: {e}")
        
        # 等待线程结束
        if hasattr(self, 'reader_thread') and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=0.5)  # 给予线程0.5秒的时间来结束
        
        event.accept()


if __name__ == '__main__':
    # 捕获未处理的异常
    def exception_hook(exctype, value, traceback):
        logger.critical(f"未捕获的异常: {exctype.__name__}: {value}")
        sys.__excepthook__(exctype, value, traceback)
    
    sys.excepthook = exception_hook
    
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())
