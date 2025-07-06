import sys
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                             QTextEdit, QLineEdit, QComboBox, QGroupBox, 
                             QFrame, QMessageBox, QScrollArea)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap

from usb_communication import USBCommunication

class StatusIndicator(QFrame):
    """状态指示器组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.connected = False
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        # 状态指示灯 - 更小
        self.status_light = QFrame()
        self.status_light.setFixedSize(12, 12)  # 更小的指示灯
        self.status_light.setFrameStyle(QFrame.NoFrame)
        
        # 状态文本 - 更小
        self.status_label = QLabel("设备未连接")
        self.status_label.setFont(QFont("Arial", 8))  # 更小的字体
        
        layout.addWidget(self.status_light)
        layout.addWidget(self.status_label)
        
        self.update_status(False)
    
    def update_status(self, connected):
        """更新连接状态"""
        self.connected = connected
        
        if connected:
            # 绿色圆形 - 已连接
            self.status_light.setStyleSheet("background-color: #00FF00; border: 1px solid #008000; border-radius: 6px;")
            self.status_label.setText("设备已连接")
            self.status_label.setStyleSheet("color: #008000; font-weight: bold;")
        else:
            # 红色圆形 - 未连接
            self.status_light.setStyleSheet("background-color: #FF0000; border: 1px solid #800000; border-radius: 6px;")
            self.status_label.setText("设备未连接")
            self.status_label.setStyleSheet("color: #800000; font-weight: bold;")

class USBGUI(QMainWindow):
    """USB通信GUI主窗口"""
    
    def __init__(self):
        super().__init__()
        self.usb_comm = USBCommunication()
        self.setup_ui()
        self.setup_connections()
        
        # 启动状态更新定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_device_status)
        self.status_timer.start(1000)  # 每秒更新一次状态
        
        # 启动完成后显示就绪状态
        QTimer.singleShot(3500, self.show_ready_status)
    
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("USB通信工具")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)  # 减少边距
        main_layout.setSpacing(5)  # 减少间距
        
        # 权限提示
        self.permission_label = QLabel("")
        self.permission_label.setAlignment(Qt.AlignCenter)
        self.permission_label.setStyleSheet("color: #E74C3C; font-weight: bold; margin: 2px;")
        main_layout.addWidget(self.permission_label)
        
        # 通信控制组
        comm_group = QGroupBox("通信控制")
        comm_group.setFont(QFont("Arial", 10, QFont.Bold))
        comm_layout = QGridLayout(comm_group)
        
        # 发送消息
        comm_layout.addWidget(QLabel("发送消息:"), 0, 0)
        self.send_input = QLineEdit()
        self.send_input.setPlaceholderText("输入要发送的消息...")
        comm_layout.addWidget(self.send_input, 0, 1)
        
        self.send_button = QPushButton("发送")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
            QPushButton:pressed {
                background-color: #21618C;
            }
        """)
        comm_layout.addWidget(self.send_button, 0, 2)
        
        # 清空按钮
        self.clear_button = QPushButton("清空")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
            QPushButton:pressed {
                background-color: #A93226;
            }
        """)
        comm_layout.addWidget(self.clear_button, 0, 3)
        
        main_layout.addWidget(comm_group)
        
        # 消息显示组
        message_group = QGroupBox("消息显示")
        message_group.setFont(QFont("Arial", 10, QFont.Bold))
        message_layout = QVBoxLayout(message_group)
        
        # 消息显示区域
        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)
        self.message_display.setFont(QFont("Consolas", 9))
        self.message_display.setStyleSheet("""
            QTextEdit {
                background-color: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        message_layout.addWidget(self.message_display)
        
        main_layout.addWidget(message_group)
        
        # 右下角状态栏
        status_layout = QHBoxLayout()
        status_layout.addStretch()  # 左侧空白
        
        # 右下角设备状态指示器
        self.device_status = StatusIndicator()
        status_layout.addWidget(self.device_status)
        
        main_layout.addLayout(status_layout)
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ECF0F1;
            }
            QGroupBox {
                background-color: white;
                border: 2px solid #BDC3C7;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLabel {
                color: #2C3E50;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #3498DB;
            }
            QComboBox {
                padding: 6px;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                background-color: white;
            }
            QComboBox:focus {
                border: 2px solid #3498DB;
            }
        """)
    
    def setup_connections(self):
        """设置信号连接"""
        # USB通信信号
        self.usb_comm.device_connected.connect(self.on_device_connected)
        self.usb_comm.device_disconnected.connect(self.on_device_disconnected)
        self.usb_comm.message_received.connect(self.on_message_received)
        self.usb_comm.error_occurred.connect(self.on_error_occurred)
        
        # GUI控件信号
        self.send_button.clicked.connect(self.send_message)
        self.clear_button.clicked.connect(self.clear_messages)
        self.send_input.returnPressed.connect(self.send_message)
    
    @pyqtSlot(str)
    def on_device_connected(self, device_name):
        """设备连接事件"""
        self.log_message(f"系统: {device_name} 已连接", "system")
        self.update_device_status()
        
        # 更新窗口标题显示设备信息
        self.setWindowTitle("USB通信工具 - VID:0x1514 PID:0x1000")
    
    @pyqtSlot(str)
    def on_device_disconnected(self, device_name):
        """设备断开事件"""
        self.log_message(f"系统: {device_name} 已断开", "system")
        self.update_device_status()
        
        # 检查是否还有其他设备连接
        connected_count = len(self.usb_comm.get_device_info())
        if connected_count == 0:
            # 没有设备连接时恢复原始标题
            self.setWindowTitle("USB通信工具")
    
    @pyqtSlot(str, bytes)
    def on_message_received(self, device_name, data):
        """消息接收事件"""
        try:
            # 尝试解码为UTF-8
            message = data.decode('utf-8')
        except UnicodeDecodeError:
            # 如果解码失败，显示十六进制
            message = data.hex()
        
        self.log_message(f"接收 [{device_name}]: {message}", "receive")
    
    @pyqtSlot(str)
    def on_error_occurred(self, error_message):
        """错误事件"""
        self.log_message(f"错误: {error_message}", "error")
        
        # 检查是否是权限错误
        if "权限不足" in error_message or "Access denied" in error_message:
            self.permission_label.setText("⚠️  权限不足！请以管理员身份运行程序")
            self.permission_label.setStyleSheet("color: #E74C3C; font-weight: bold; margin: 5px; background-color: #FADBD8; padding: 5px; border-radius: 3px;")
        else:
            self.permission_label.setText("")
            self.permission_label.setStyleSheet("color: #E74C3C; font-weight: bold; margin: 5px;")
    
    def send_message(self):
        """发送消息"""
        message = self.send_input.text().strip()
        if not message:
            return
        
        # 使用设备索引0（唯一设备）
        device_index = 0
        
        # 检查设备是否连接
        if not self.usb_comm.is_device_connected(device_index):
            QMessageBox.warning(self, "警告", "设备未连接！")
            return
        
        # 检查是否为只读接口
        if self.usb_comm.is_device_readonly(device_index):
            QMessageBox.information(self, "只读接口", 
                "当前设备为只读接口，无法发送数据。\n\n"
                "此接口只能接收设备发送的数据，不能向设备发送命令。\n\n"
                "建议开启自动查询模式来监听设备数据。")
            return
        
        # 发送消息
        if self.usb_comm.send_message(device_index, message):
            self.log_message(f"发送: {message}", "send")
        else:
            QMessageBox.critical(self, "错误", "发送消息失败！")
    
    def clear_messages(self):
        """清空消息显示"""
        self.message_display.clear()
    
    def show_ready_status(self):
        """显示就绪状态"""
        connected_count = len(self.usb_comm.get_device_info())
        if connected_count > 0:
            self.log_message(f"系统就绪，检测到 {connected_count} 个设备", "system")
    
    def log_message(self, message, message_type="info"):
        """记录消息到显示区域"""
        timestamp = time.strftime("%H:%M:%S")
        
        # 根据消息类型设置颜色
        color_map = {
            "send": "#2980B9",      # 蓝色 - 发送
            "receive": "#27AE60",   # 绿色 - 接收
            "system": "#F39C12",    # 橙色 - 系统
            "error": "#E74C3C",     # 红色 - 错误
            "info": "#2C3E50"       # 深灰 - 信息
        }
        
        color = color_map.get(message_type, "#2C3E50")
        formatted_message = f'<span style="color: {color};">[{timestamp}] {message}</span>'
        
        self.message_display.append(formatted_message)
        
        # 自动滚动到底部
        scrollbar = self.message_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_device_status(self):
        """更新设备状态显示"""
        # 更新设备状态（只检查索引0的设备）
        device_connected = self.usb_comm.is_device_connected(0)
        self.device_status.update_status(device_connected)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 清理USB通信资源
        self.usb_comm.cleanup()
        event.accept()

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("USB通信工具")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("STM32PD_sniffer")
    
    # 创建并显示主窗口
    window = USBGUI()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()