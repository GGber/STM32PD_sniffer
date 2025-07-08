import sys
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                             QLineEdit, QComboBox, QGroupBox, 
                             QFrame, QMessageBox, QScrollArea, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap

from usb_communication import USBCommunication
from pd_parser import parse_pd_data  # 新增：导入PD数据解析函数

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
        self.setGeometry(100, 100, 900, 650)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)
        
        # 权限提示
        self.permission_label = QLabel("")
        self.permission_label.setAlignment(Qt.AlignCenter)
        self.permission_label.setStyleSheet("color: #E74C3C; font-weight: bold; margin: 2px;")
        main_layout.addWidget(self.permission_label)
        
        # 通信控制组
        comm_group = QGroupBox("通信控制")
        comm_group.setFont(QFont("Arial", 11, QFont.Bold))
        comm_group.setStyleSheet("""
            QGroupBox {
                background-color: #F8FAFF;
                border: 2px solid #A9CCE3;
                border-radius: 10px;
                margin-top: 8px;
                padding-top: 8px;
                box-shadow: 0 2px 8px #D6EAF8;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        comm_layout = QGridLayout(comm_group)
        comm_layout.setHorizontalSpacing(10)
        comm_layout.setVerticalSpacing(8)
        
        # 发送消息
        comm_layout.addWidget(QLabel("发送消息:"), 0, 0)
        self.send_input = QLineEdit()
        self.send_input.setPlaceholderText("输入要发送的消息...")
        self.send_input.setStyleSheet("padding: 8px; border: 1.5px solid #A9CCE3; border-radius: 6px; background-color: #FDFEFE;")
        comm_layout.addWidget(self.send_input, 0, 1)
        
        self.send_button = QPushButton("发送")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #5DADE2;
                color: white;
                border: none;
                padding: 10px 22px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 15px;
                letter-spacing: 1px;
                box-shadow: 0 2px 6px #D6EAF8;
            }
            QPushButton:hover {
                background-color: #3498DB;
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
                padding: 10px 22px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 15px;
                letter-spacing: 1px;
                box-shadow: 0 2px 6px #FADBD8;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
            QPushButton:pressed {
                background-color: #922B21;
            }
        """)
        comm_layout.addWidget(self.clear_button, 0, 3)
        
        main_layout.addWidget(comm_group)
        
        # 消息显示组（表格控件）
        message_group = QGroupBox("PD数据包列表")
        message_group.setFont(QFont("Arial", 11, QFont.Bold))
        message_group.setStyleSheet("""
            QGroupBox {
                background-color: #F8FAFF;
                border: 2px solid #A9CCE3;
                border-radius: 10px;
                margin-top: 8px;
                padding-top: 8px;
                box-shadow: 0 2px 8px #D6EAF8;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        message_layout = QVBoxLayout(message_group)
        self.pd_table = QTableWidget()
        self.pd_table.setColumnCount(8)
        self.pd_table.setHorizontalHeaderLabels([
            "时间戳", "SOP类型", "消息类型", "供电角色", "协议版本", "数据角色", "ID", "详细内容"
        ])
        self.pd_table.setColumnWidth(7, 420)
        self.pd_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.pd_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.pd_table.setSelectionMode(QTableWidget.SingleSelection)
        self.pd_table.verticalHeader().setVisible(False)
        self.pd_table.setAlternatingRowColors(True)
        self.pd_table.setStyleSheet("""
            QTableWidget {
                background-color: #FDFEFE;
                border: 1.5px solid #A9CCE3;
                border-radius: 8px;
                font-family: Consolas, Arial, sans-serif;
                font-size: 13px;
                selection-background-color: #D6EAF8;
                selection-color: #222222;
                gridline-color: #D6EAF8;
            }
            QHeaderView::section {
                background-color: #5DADE2;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: none;
                height: 32px;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:alternate {
                background: #EBF5FB;
            }
        """)
        self.pd_table.horizontalHeader().setStyleSheet("background-color: #5DADE2; color: white; font-weight: bold; font-size: 14px; border: none; height: 32px;")
        self.pd_table.setAlternatingRowColors(True)
        message_layout.addWidget(self.pd_table)
        main_layout.addWidget(message_group)
        
        # 右下角状态栏
        status_layout = QHBoxLayout()
        status_layout.addStretch()  # 左侧空白
        
        # 右下角设备状态指示器
        self.device_status = StatusIndicator()
        status_layout.addWidget(self.device_status)
        
        main_layout.addLayout(status_layout)
        
        # 主窗口背景渐变
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #F8FAFF, stop:1 #D6EAF8);
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
        self.setWindowTitle("USB通信工具 - PD Sniffer")
    
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
        result = parse_pd_data(data)
        # 非PD包直接忽略不显示
        if result.get('error') and '非PD包' in result.get('error_msg', ''):
            return
        field_values = [''] * 8
        error_flag = result.get('error', False)
        # 时间戳
        if result.get('timestamp') is not None:
            ms = result['timestamp']
            m = (ms // 1000) // 60
            s = (ms // 1000) % 60
            ms_rem = ms % 1000
            field_values[0] = f"{m:02d}:{s:02d}.{ms_rem:03d}"
        # SOP类型
        field_values[1] = result.get('sop_type', '')
        # 消息类型
        field_values[2] = result.get('msg_type', '')
        # 供电角色
        field_values[3] = result.get('power_role', '')
        # 协议版本
        field_values[4] = result.get('spec_revision', '')
        # 数据角色
        field_values[5] = result.get('data_role', '')
        # ID
        field_values[6] = str(result.get('msg_id', ''))
        # 详细内容加粗Header Data CRC
        detail = ''
        raw_hex = result.get('raw_hex', '')
        if raw_hex:
            hex_parts = raw_hex.split()
            if len(hex_parts) > 10:
                header_hex = ' '.join(hex_parts[4:6])
                data_hex = ' '.join(hex_parts[6:-4])
                crc_hex = ' '.join(hex_parts[-4:])
                detail += f"Header: {header_hex}    Data: {data_hex} CRC: {crc_hex}"
            elif len(hex_parts) > 6:
                header_hex = ' '.join(hex_parts[4:6])
                data_hex = ' '.join(hex_parts[6:])
                detail += f"Header: {header_hex}    Data: {data_hex}"
            else:
                detail += f"Header: {raw_hex}"
        # 协议字段解析，去掉消息类型主行
        proto = result.get('detail', '')
        if proto:
            lines = str(proto).split('\n')
            proto_lines = []
            for l in lines:
                # 跳过第一行（如GoodCRC、Request等）
                if proto_lines or (not (l.strip().startswith('GoodCRC') or l.strip().startswith('Request') or l.strip().startswith('Accept') or l.strip().startswith('Reject') or l.strip().startswith('Ping') or l.strip().startswith('PS_RDY') or l.strip().startswith('GotoMin') or l.strip().startswith('DR_Swap') or l.strip().startswith('PR_Swap') or l.strip().startswith('VCONN_Swap') or l.strip().startswith('Wait') or l.strip().startswith('Soft_Reset') or l.strip().startswith('Not_Supported') or l.strip().startswith('Get_Source_Cap') or l.strip().startswith('Get_Sink_Cap') or l.strip().startswith('Get_Source_Cap_Ext') or l.strip().startswith('Source Capabilities') or l.strip().startswith('Sink Capabilities') or l.strip().startswith('Vendor Defined'))):
                    proto_lines.append(l)
            proto_str = '\n'.join(proto_lines)
            if proto_str:
                if detail:
                    detail += ' '
                detail += proto_str
        if result.get('error') and result.get('error_msg'):
            detail = result['error_msg']
        field_values[7] = detail
        row = self.pd_table.rowCount()
        self.pd_table.insertRow(row)
        for col, val in enumerate(field_values):
            item = QTableWidgetItem(val)
            if col == 7:
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
            else:
                item.setTextAlignment(Qt.AlignCenter)
            self.pd_table.setItem(row, col, item)
        # 根据供电角色设置行背景色
        role_lower = (field_values[3] or '').lower()
        if role_lower == 'source':
            for col in range(self.pd_table.columnCount()):
                self.pd_table.item(row, col).setBackground(QColor(Qt.cyan).lighter(180))  # 淡蓝色
        elif role_lower == 'sink':
            for col in range(self.pd_table.columnCount()):
                self.pd_table.item(row, col).setBackground(QColor(Qt.green).lighter(180))  # 淡绿色
        if error_flag:
            for col in range(self.pd_table.columnCount()):
                self.pd_table.item(row, col).setBackground(Qt.red)
        self.pd_table.scrollToBottom()
    
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
        self.pd_table.setRowCount(0)
    
    def show_ready_status(self):
        """显示就绪状态"""
        connected_count = len(self.usb_comm.get_device_info())
        if connected_count > 0:
            self.log_message(f"系统就绪，检测到 {connected_count} 个设备", "system")
    
    def log_message(self, message, message_type="info"):
        pass  # 表格模式下不再使用日志显示
    
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