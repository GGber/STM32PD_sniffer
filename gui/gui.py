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
    
    def __init__(self, device_name, parent=None):
        super().__init__(parent)
        self.device_name = device_name
        self.connected = False
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        # 状态指示灯
        self.status_light = QFrame()
        self.status_light.setFixedSize(20, 20)
        self.status_light.setFrameStyle(QFrame.Box)
        self.status_light.setLineWidth(2)
        
        # 设备名称标签
        self.name_label = QLabel(self.device_name)
        self.name_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        # 状态文本
        self.status_label = QLabel("未连接")
        self.status_label.setFont(QFont("Arial", 9))
        
        layout.addWidget(self.status_light)
        layout.addWidget(self.name_label)
        layout.addWidget(self.status_label)
        layout.addStretch()
        
        self.update_status(False)
    
    def update_status(self, connected):
        """更新连接状态"""
        self.connected = connected
        
        if connected:
            # 绿色 - 已连接
            self.status_light.setStyleSheet("background-color: #00FF00; border: 2px solid #008000;")
            self.status_label.setText("已连接")
            self.status_label.setStyleSheet("color: #008000; font-weight: bold;")
        else:
            # 红色 - 未连接
            self.status_light.setStyleSheet("background-color: #FF0000; border: 2px solid #800000;")
            self.status_label.setText("未连接")
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
        
        # 初始化完成后更新状态
        QTimer.singleShot(3000, self.update_status_label)
        
        # 启动完成后显示就绪状态
        QTimer.singleShot(3500, self.show_ready_status)
    
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("USB通信工具 - VID:0x1514 PID:0x1000")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 标题
        title_label = QLabel("USB通信工具")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2C3E50; margin: 10px;")
        main_layout.addWidget(title_label)
        
        # 权限提示
        self.permission_label = QLabel("")
        self.permission_label.setAlignment(Qt.AlignCenter)
        self.permission_label.setStyleSheet("color: #E74C3C; font-weight: bold; margin: 5px;")
        main_layout.addWidget(self.permission_label)
        
        # 状态提示
        self.status_label = QLabel("正在初始化USB设备...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #3498DB; font-weight: bold; margin: 5px; background-color: #EBF3FD; padding: 5px; border-radius: 3px;")
        main_layout.addWidget(self.status_label)
        
        # 设备信息组
        device_group = QGroupBox("设备信息")
        device_group.setFont(QFont("Arial", 10, QFont.Bold))
        device_layout = QGridLayout(device_group)
        
        # VID/PID信息
        vid_label = QLabel("VID: 0x1514")
        pid_label = QLabel("PID: 0x1000")
        vid_label.setFont(QFont("Arial", 9))
        pid_label.setFont(QFont("Arial", 9))
        
        device_layout.addWidget(QLabel("设备标识:"), 0, 0)
        device_layout.addWidget(vid_label, 0, 1)
        device_layout.addWidget(pid_label, 0, 2)
        
        main_layout.addWidget(device_group)
        
        # 设备状态组
        status_group = QGroupBox("设备状态")
        status_group.setFont(QFont("Arial", 10, QFont.Bold))
        status_layout = QVBoxLayout(status_group)
        
        # 创建状态指示器
        self.device1_status = StatusIndicator("WinUSB设备1")
        self.device2_status = StatusIndicator("WinUSB设备2")
        
        status_layout.addWidget(self.device1_status)
        status_layout.addWidget(self.device2_status)
        
        main_layout.addWidget(status_group)
        
        # 通信控制组
        comm_group = QGroupBox("通信控制")
        comm_group.setFont(QFont("Arial", 10, QFont.Bold))
        comm_layout = QGridLayout(comm_group)
        
        # 目标设备选择
        comm_layout.addWidget(QLabel("目标设备:"), 0, 0)
        self.device_combo = QComboBox()
        self.device_combo.addItems(["WinUSB设备1", "WinUSB设备2"])
        comm_layout.addWidget(self.device_combo, 0, 1)
        
        # 发送消息
        comm_layout.addWidget(QLabel("发送消息:"), 1, 0)
        self.send_input = QLineEdit()
        self.send_input.setPlaceholderText("输入要发送的消息...")
        comm_layout.addWidget(self.send_input, 1, 1)
        
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
        comm_layout.addWidget(self.send_button, 1, 2)
        
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
        comm_layout.addWidget(self.clear_button, 1, 3)
        
        # 查询控制
        comm_layout.addWidget(QLabel("查询控制:"), 2, 0)
        
        # 自动查询开关
        self.auto_query_checkbox = QPushButton("自动查询: 关闭")
        self.auto_query_checkbox.setCheckable(True)
        self.auto_query_checkbox.setChecked(False)
        self.auto_query_checkbox.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #27AE60;
            }
            QPushButton:!checked {
                background-color: #95A5A6;
            }
        """)
        comm_layout.addWidget(self.auto_query_checkbox, 2, 1)
        
        # 手动查询按钮
        self.query_button = QPushButton("手动查询")
        self.query_button.setStyleSheet("""
            QPushButton {
                background-color: #F39C12;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E67E22;
            }
            QPushButton:pressed {
                background-color: #D35400;
            }
        """)
        comm_layout.addWidget(self.query_button, 2, 2)
        
        # 测试按钮
        self.test_button = QPushButton("测试通信")
        self.test_button.setStyleSheet("""
            QPushButton {
                background-color: #E67E22;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D35400;
            }
            QPushButton:pressed {
                background-color: #BA4A00;
            }
        """)
        comm_layout.addWidget(self.test_button, 2, 3)
        
        # 调试按钮
        self.debug_button = QPushButton("调试信息")
        self.debug_button.setStyleSheet("""
            QPushButton {
                background-color: #9B59B6;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
            QPushButton:pressed {
                background-color: #7D3C98;
            }
        """)
        comm_layout.addWidget(self.debug_button, 2, 4)
        
        # 调试模式开关
        self.debug_mode_button = QPushButton("调试模式: 关闭")
        self.debug_mode_button.setCheckable(True)
        self.debug_mode_button.setChecked(False)
        self.debug_mode_button.setStyleSheet("""
            QPushButton {
                background-color: #95A5A6;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #E67E22;
            }
            QPushButton:!checked {
                background-color: #95A5A6;
            }
        """)
        comm_layout.addWidget(self.debug_mode_button, 2, 5)
        
        main_layout.addWidget(comm_group)
        
        # 消息显示组
        message_group = QGroupBox("消息记录")
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
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ECF0F1;
            }
            QGroupBox {
                background-color: white;
                border: 2px solid #BDC3C7;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
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
        self.auto_query_checkbox.toggled.connect(self.toggle_auto_query)
        self.query_button.clicked.connect(self.manual_query)
        self.test_button.clicked.connect(self.test_communication)
        self.debug_button.clicked.connect(self.show_debug_info)
        self.debug_mode_button.toggled.connect(self.toggle_debug_mode)
    
    @pyqtSlot(str)
    def on_device_connected(self, device_name):
        """设备连接事件"""
        self.log_message(f"系统: {device_name} 已连接", "system")
        self.update_device_status()
        self.update_status_label()
    
    @pyqtSlot(str)
    def on_device_disconnected(self, device_name):
        """设备断开事件"""
        self.log_message(f"系统: {device_name} 已断开", "system")
        self.update_device_status()
        self.update_status_label()
    
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
        
        # 获取目标设备索引
        device_index = self.device_combo.currentIndex()
        
        # 检查设备是否连接
        if not self.usb_comm.is_device_connected(device_index):
            QMessageBox.warning(self, "警告", f"{self.device_combo.currentText()} 未连接！")
            return
        
        # 发送消息
        if self.usb_comm.send_message(device_index, message):
            self.log_message(f"发送 [{self.device_combo.currentText()}]: {message}", "send")
            self.send_input.clear()
        else:
            QMessageBox.critical(self, "错误", "发送消息失败！")
    
    def clear_messages(self):
        """清空消息显示"""
        self.message_display.clear()
    
    def toggle_auto_query(self, checked):
        """切换自动查询状态"""
        self.usb_comm.set_auto_query(checked)
        if checked:
            self.auto_query_checkbox.setText("自动查询: 开启")
            self.auto_query_checkbox.setStyleSheet("""
                QPushButton {
                    background-color: #27AE60;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
            self.log_message("自动查询已开启", "system")
        else:
            self.auto_query_checkbox.setText("自动查询: 关闭")
            self.auto_query_checkbox.setStyleSheet("""
                QPushButton {
                    background-color: #95A5A6;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
            self.log_message("自动查询已关闭", "system")
    
    def manual_query(self):
        """手动查询数据"""
        device_index = self.device_combo.currentIndex()
        if self.usb_comm.manual_query(device_index):
            self.log_message(f"手动查询 [{self.device_combo.currentText()}] 成功", "system")
        else:
            self.log_message(f"手动查询 [{self.device_combo.currentText()}] 失败", "error")
    
    def toggle_debug_mode(self, checked):
        """切换调试模式"""
        self.usb_comm.debug_mode = checked
        if checked:
            self.debug_mode_button.setText("调试模式: 开启")
            self.debug_mode_button.setStyleSheet("""
                QPushButton {
                    background-color: #E67E22;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
            self.log_message("调试模式已开启", "system")
        else:
            self.debug_mode_button.setText("调试模式: 关闭")
            self.debug_mode_button.setStyleSheet("""
                QPushButton {
                    background-color: #95A5A6;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
            self.log_message("调试模式已关闭", "system")
    
    def test_communication(self):
        """测试通信功能"""
        device_index = self.device_combo.currentIndex()
        device_name = self.device_combo.currentText()
        
        self.log_message(f"开始测试 [{device_name}] 通信...", "system")
        
        # 临时关闭自动查询，避免干扰测试
        original_auto_query = self.usb_comm.auto_query
        self.usb_comm.auto_query = False
        
        # 测试1: 发送简单命令
        test_commands = [
            b'\x01',  # 简单查询
            b'\x02',  # 另一个命令
            b'TEST',  # 文本命令
            b'\x00',  # 空命令
        ]
        
        success_count = 0
        response_count = 0
        
        for i, cmd in enumerate(test_commands):
            try:
                self.log_message(f"测试命令 {i+1}: {cmd.hex() if isinstance(cmd, bytes) else cmd}", "system")
                
                # 发送命令
                if self.usb_comm.send_message(device_index, cmd):
                    self.log_message(f"命令 {i+1} 发送成功", "send")
                    success_count += 1
                    
                    # 等待响应
                    import time
                    time.sleep(0.2)
                    
                    # 尝试读取响应
                    if self.usb_comm.manual_query(device_index):
                        self.log_message(f"命令 {i+1} 响应成功", "receive")
                        response_count += 1
                    else:
                        self.log_message(f"命令 {i+1} 无响应", "error")
                else:
                    self.log_message(f"命令 {i+1} 发送失败", "error")
                    
            except Exception as e:
                self.log_message(f"命令 {i+1} 测试异常: {e}", "error")
        
        # 恢复原来的自动查询状态
        self.usb_comm.auto_query = original_auto_query
        
        # 显示测试总结
        total_commands = len(test_commands)
        self.log_message(f"=== 通信测试总结 ===", "system")
        self.log_message(f"发送成功率: {success_count}/{total_commands} ({success_count/total_commands*100:.1f}%)", "system")
        self.log_message(f"响应成功率: {response_count}/{total_commands} ({response_count/total_commands*100:.1f}%)", "system")
        self.log_message(f"[{device_name}] 通信测试完成", "system")
    
    def show_ready_status(self):
        """显示就绪状态"""
        connected_count = len(self.usb_comm.get_device_info())
        if connected_count > 0:
            self.log_message(f"系统就绪，检测到 {connected_count} 个设备", "system")
    
    def show_debug_info(self):
        """显示调试信息"""
        device_info = self.usb_comm.get_device_info()
        
        debug_msg = "=== 设备调试信息 ===\n"
        debug_msg += f"已连接设备数量: {len(device_info)}\n"
        
        for index, info in device_info.items():
            debug_msg += f"设备{index}: {info['name']} (ID: {info['id']})\n"
        
        debug_msg += f"\n设备1连接状态: {self.usb_comm.is_device_connected(0)}\n"
        debug_msg += f"设备2连接状态: {self.usb_comm.is_device_connected(1)}\n"
        
        # 扫描所有USB设备
        all_devices = self.usb_comm.scan_all_devices()
        debug_msg += f"\n=== 所有USB设备 ===\n"
        debug_msg += f"系统USB设备总数: {len(all_devices)}\n"
        
        target_count = 0
        for device in all_devices:
            status = "✓" if device['is_target'] else "✗"
            debug_msg += f"{status} VID={device['vid']}, PID={device['pid']}, Bus={device['bus']}, Address={device['address']}\n"
            if device['is_target']:
                target_count += 1
        
        debug_msg += f"\n目标设备(VID=0x1514, PID=0x1000)数量: {target_count}\n"
        
        # 检查驱动状态
        try:
            driver_status = self.usb_comm.check_device_driver()
            debug_msg += f"\n=== 驱动状态 ===\n"
            debug_msg += f"设备驱动状态: {driver_status}\n"
        except:
            debug_msg += f"\n=== 驱动状态 ===\n"
            debug_msg += f"无法检查驱动状态\n"
        
        # 显示在消息区域
        self.log_message(debug_msg, "info")
    
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
        # 更新设备1状态
        device1_connected = self.usb_comm.is_device_connected(0)
        self.device1_status.update_status(device1_connected)
        
        # 更新设备2状态
        device2_connected = self.usb_comm.is_device_connected(1)
        self.device2_status.update_status(device2_connected)
    
    def update_status_label(self):
        """更新状态标签"""
        connected_count = len(self.usb_comm.get_device_info())
        
        if connected_count == 0:
            self.status_label.setText("未检测到设备")
            self.status_label.setStyleSheet("color: #E74C3C; font-weight: bold; margin: 5px; background-color: #FADBD8; padding: 5px; border-radius: 3px;")
        elif connected_count == 1:
            self.status_label.setText("检测到1个设备")
            self.status_label.setStyleSheet("color: #F39C12; font-weight: bold; margin: 5px; background-color: #FEF9E7; padding: 5px; border-radius: 3px;")
        elif connected_count == 2:
            self.status_label.setText("检测到2个设备 - 就绪")
            self.status_label.setStyleSheet("color: #27AE60; font-weight: bold; margin: 5px; background-color: #E8F8F5; padding: 5px; border-radius: 3px;")
        else:
            self.status_label.setText(f"检测到{connected_count}个设备")
            self.status_label.setStyleSheet("color: #3498DB; font-weight: bold; margin: 5px; background-color: #EBF3FD; padding: 5px; border-radius: 3px;")
    
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
