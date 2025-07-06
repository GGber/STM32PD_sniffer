import usb.core
import usb.util
import usb.backend.libusb1
import threading
import time
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import win32file
import win32api
import win32con
import pywintypes

class USBCommunication(QObject):
    """USB通信类，支持热拔插和双winusb设备"""
    
    # 信号定义
    device_connected = pyqtSignal(str)  # 设备连接信号
    device_disconnected = pyqtSignal(str)  # 设备断开信号
    message_received = pyqtSignal(str, bytes)  # 消息接收信号 (设备名, 数据)
    error_occurred = pyqtSignal(str)  # 错误信号
    
    def __init__(self):
        super().__init__()
        self.vid = 0x1514
        self.pid = 0x1000
        self.devices = {}  # 存储连接的设备
        self.device_handles = {}  # 存储设备句柄
        self.monitoring = False
        self.monitor_thread = None
        
        # 设备名称映射
        self.device_names = {
            0: "USB设备"
        }
        

        self.filter_empty_data = True  # 过滤空数据
        
        # 检查权限
        self.check_permissions()
        
        # 强制指定libusb1后端，并指定dll路径
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        dll_path = os.path.join(current_dir, "libusb-1.0.dll")
        
        self.backend = usb.backend.libusb1.get_backend(find_library=lambda x: dll_path)
        if self.backend is None:
            self.error_occurred.emit(f"libusb-1.0.dll未找到或无法加载！\n请确认文件存在于: {dll_path}")
            raise RuntimeError(f"libusb-1.0.dll未找到或无法加载: {dll_path}")
        
        # 延迟启动设备监控，避免启动时的权限检查冲突
        QTimer.singleShot(2000, self.start_device_monitoring)
    
    def check_permissions(self):
        """检查USB设备访问权限"""
        try:
            print("开始权限检查...")
            # 尝试访问一个USB设备来检查权限
            test_devices = list(usb.core.find(find_all=True, backend=self.backend))
            print(f"找到 {len(test_devices)} 个USB设备")
            
            if test_devices:
                # 尝试读取第一个设备的VID/PID
                test_device = test_devices[0]
                try:
                    vid = test_device.idVendor
                    pid = test_device.idProduct
                    print(f"权限检查通过，可以访问USB设备 VID=0x{vid:04X}, PID=0x{pid:04X}")
                    
                    # 尝试访问目标设备
                    target_devices = list(usb.core.find(find_all=True, idVendor=self.vid, idProduct=self.pid, backend=self.backend))
                    print(f"找到 {len(target_devices)} 个目标设备 (VID=0x{self.vid:04X}, PID=0x{self.pid:04X})")
                    
                    for i, device in enumerate(target_devices):
                        try:
                            print(f"目标设备 {i}: Bus={device.bus}, Address={device.address}")
                            # 尝试获取配置
                            cfg = device.get_active_configuration()
                            print(f"  配置获取成功: {cfg}")
                            print(f"  接口数量: {cfg.bNumInterfaces}")
                        except Exception as e:
                            print(f"  访问目标设备失败: {e}")
                            if "Access denied" in str(e) or "insufficient permissions" in str(e):
                                print("⚠️  目标设备权限不足！")
                                self.error_occurred.emit("⚠️  目标设备权限不足！请检查设备驱动")
                            else:
                                print(f"  其他错误: {e}")
                                self.error_occurred.emit(f"设备访问错误: {e}")
                    
                except Exception as e:
                    if "Access denied" in str(e) or "insufficient permissions" in str(e):
                        print("⚠️  权限不足警告：无法访问USB设备")
                        self.error_occurred.emit("⚠️  权限不足！请以管理员身份运行程序")
                        print("解决方案：")
                        print("1. 右键点击程序，选择'以管理员身份运行'")
                        print("2. 或者在命令提示符中以管理员身份运行：python gui.py")
                        print("3. 检查设备驱动是否正确安装")
                    else:
                        print(f"权限检查其他错误: {e}")
                        self.error_occurred.emit(f"权限检查失败: {e}")
            else:
                print("未找到任何USB设备")
                self.error_occurred.emit("未找到任何USB设备，请检查设备连接")
        except Exception as e:
            print(f"权限检查失败: {e}")
            self.error_occurred.emit("USB设备访问失败，请检查权限")
    
    def start_device_monitoring(self):
        """启动设备监控线程"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_devices, daemon=True)
            self.monitor_thread.start()
    
    def stop_device_monitoring(self):
        """停止设备监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_devices(self):
        """监控设备连接状态"""
        while self.monitoring:
            try:
                # 查找所有匹配的设备，强制指定backend
                devices = list(usb.core.find(find_all=True, idVendor=self.vid, idProduct=self.pid, backend=self.backend))
                
                # 添加调试信息
                if len(devices) > 0:
                    for i, device in enumerate(devices):
                        # print(f"找到目标设备 {i+1}: VID=0x{device.idVendor:04X}, PID=0x{device.idProduct:04X}, Bus={device.bus}, Address={device.address}")
                        
                        # 检查每个设备的接口（只在第一次连接时）
                        if not any(f"{device.bus}-{device.address}" in dev_id for dev_id in self.devices.keys()):
                            try:
                                cfg = device.get_active_configuration()
                                print(f"  配置: {cfg}")
                                for intf_num in range(cfg.bNumInterfaces):
                                    intf = cfg[intf_num, 0]
                                    print(f"  接口 {intf_num}: {intf}")
                                    
                                    # 检查接口的端点
                                    for ep in intf:
                                        print(f"    端点: {ep.bEndpointAddress} (方向: {'IN' if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN else 'OUT'})")
                            except Exception as e:
                                print(f"  检查接口时出错: {e}")
                                if "Access denied" in str(e):
                                    print("  ⚠️  权限不足，但已建立的连接可能仍然有效")
                                elif "insufficient permissions" in str(e):
                                    print("  ⚠️  权限不足，但已建立的连接可能仍然有效")
                
                # 检查新连接的设备
                # 获取当前已连接的设备索引
                used_indices = set()
                for device_info in self.devices.values():
                    used_indices.add(device_info['index'])
                
                # 为每个物理设备创建多个接口连接
                for device in devices:
                    device_id = f"{device.bus}-{device.address}"
                    
                    try:
                        # 只在第一次连接时检查配置，避免重复权限检查
                        if not any(device_id in dev_id for dev_id in self.devices.keys()):
                            cfg = device.get_active_configuration()
                            # 只连接接口0
                            interfaces_to_connect = [(0, 0)]
                            
                            for intf_num, alt_setting in interfaces_to_connect:
                                interface_id = f"{device_id}-{intf_num}"
                                
                                if interface_id not in self.devices:
                                    # 找到第一个可用的索引
                                    available_index = 0
                                    while available_index in used_indices:
                                        available_index += 1
                                    
                                    print(f"尝试连接接口: {interface_id}, 分配索引: {available_index}")
                                    self._connect_device_interface(device, available_index, intf_num, alt_setting)
                                    used_indices.add(available_index)
                                else:
                                    print(f"接口已连接: {interface_id}")

                    except Exception as e:
                        print(f"处理设备接口时出错: {e}")
                        if "Access denied" in str(e) or "insufficient permissions" in str(e):
                            print("⚠️  权限不足，但已建立的连接可能仍然有效")
                            # 不发送错误信号，因为已建立的连接可能仍然有效
                
                # 检查断开的设备
                disconnected_devices = []
                for device_id in list(self.devices.keys()):
                    # 检查设备是否仍然存在
                    device_still_exists = False
                    for device in devices:
                        if f"{device.bus}-{device.address}" in device_id:
                            device_still_exists = True
                            break
                    
                    if not device_still_exists:
                        disconnected_devices.append(device_id)
                
                # 断开不再存在的设备
                for device_id in disconnected_devices:
                    self._disconnect_device(device_id)
                
                time.sleep(1)  # 1秒检查间隔
                
            except Exception as e:
                print(f"设备监控异常: {e}")
                time.sleep(1)  # 异常时也等待1秒
    
    def _connect_device_interface(self, device, index, interface_num, alt_setting):
        """连接设备的特定接口"""
        try:
            interface_id = f"{device.bus}-{device.address}-{interface_num}"
            device_name = self.device_names.get(index, f"WinUSB设备{index+1}")
            
            print(f"开始连接接口 {device_name} (ID: {interface_id})")
            
            # 检查设备是否已经被其他进程占用
            try:
                device.set_configuration()
                print(f"设备配置设置成功: {device_name}")
            except Exception as e:
                print(f"设备配置失败: {device_name}, 错误: {str(e)}")
                self.error_occurred.emit(f"设备配置失败 ({device_name}): {str(e)}")
                return
            
            # 获取USB端点
            handle = self._get_winusb_handle_for_interface(device, interface_num, alt_setting)
            if handle:
                self.devices[interface_id] = {
                    'device': device,
                    'name': device_name,
                    'index': index,
                    'handle': handle,
                    'interface': interface_num
                }
                self.device_handles[interface_id] = handle
                
                print(f"接口端点获取成功: {device_name}")
                
                # 启动接收线程
                receive_thread = threading.Thread(
                    target=self._receive_messages, 
                    args=(interface_id,), 
                    daemon=True
                )
                receive_thread.start()
                
                self.device_connected.emit(device_name)
                print(f"接口已连接: {device_name} (ID: {interface_id})")
            else:
                print(f"接口端点获取失败: {device_name}")
                self.error_occurred.emit(f"接口端点获取失败: {device_name}")
            
        except Exception as e:
            print(f"连接接口异常: {device_name}, 错误: {str(e)}")
            self.error_occurred.emit(f"连接接口失败 ({device_name}): {str(e)}")
    
    def _connect_device(self, device, index):
        """连接设备（保持向后兼容）"""
        self._connect_device_interface(device, index, 0, 0)
    
    def _disconnect_device(self, device_id):
        """断开设备"""
        try:
            if device_id in self.devices:
                device_info = self.devices[device_id]
                device_name = device_info['name']
                
                # 关闭句柄
                if device_id in self.device_handles:
                    try:
                        # 释放USB设备
                        handle_info = self.device_handles[device_id]
                        usb.util.dispose_resources(handle_info['device'])
                    except:
                        pass
                    del self.device_handles[device_id]
                
                del self.devices[device_id]
                self.device_disconnected.emit(device_name)
                print(f"设备已断开: {device_name} (ID: {device_id})")
                
        except Exception as e:
            self.error_occurred.emit(f"断开设备失败: {str(e)}")
    
    def _get_winusb_handle_for_interface(self, device, interface_num, alt_setting):
        """获取特定接口的WinUSB句柄"""
        try:
            # 获取配置
            cfg = device.get_active_configuration()
            print(f"设备配置: {cfg}")
            
            # 查找指定接口
            intf = cfg[(interface_num, alt_setting)]
            print(f"接口 {interface_num}: {intf}")
            
            # 查找输入端点 (IN)
            ep_in = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: 
                    usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
            )
            
            # 查找输出端点 (OUT)
            ep_out = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: 
                    usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
            )
            
            print(f"接口 {interface_num} 输入端点: {ep_in}")
            print(f"接口 {interface_num} 输出端点: {ep_out}")
            
            if ep_in is None or ep_out is None:
                self.error_occurred.emit(f"接口 {interface_num} 未找到USB端点")
                return None
            
            # 返回设备对象和端点信息
            return {
                'device': device,
                'ep_in': ep_in,
                'ep_out': ep_out
            }
            
        except Exception as e:
            print(f"获取接口 {interface_num} USB端点异常: {str(e)}")
            self.error_occurred.emit(f"获取接口 {interface_num} USB设备失败: {str(e)}")
            return None
    
    def _get_winusb_handle(self, device):
        """获取WinUSB句柄（保持向后兼容）"""
        return self._get_winusb_handle_for_interface(device, 0, 0)
    
    def _receive_messages(self, device_id):
        """接收消息线程 - 1ms轮询方式"""
        print(f"启动接收线程: {device_id}")
        
        while device_id in self.devices and self.monitoring:
            try:
                if device_id in self.device_handles:
                    handle_info = self.device_handles[device_id]
                    device_info = self.devices[device_id]
                    
                    # 持续监听设备数据，使用1ms轮询
                    try:
                        # 尝试读取设备发送的数据
                        data = handle_info['ep_in'].read(64, timeout=1)  # 1ms超时
                        if data and len(data) > 0:
                            # 将array.array转换为bytes
                            if hasattr(data, 'tobytes'):
                                data_bytes = data.tobytes()
                            else:
                                data_bytes = bytes(data)
                            
                            # 过滤掉空数据或无效数据
                            if self.filter_empty_data:
                                if data_bytes and len(data_bytes.strip(b'\x00')) > 0:
                                    self.message_received.emit(device_info['name'], data_bytes)
                            else:
                                self.message_received.emit(device_info['name'], data_bytes)
                        
                    except usb.core.USBError as e:
                        # USB超时是正常的，不报错
                        if e.args == ('Operation timed out',):
                            pass
                        elif "Operation not supported" in str(e):
                            # 某些操作不支持，静默处理
                            pass
                        else:
                            # 静默处理其他错误
                            pass
                
                time.sleep(0.001)  # 1ms轮询间隔
                
            except Exception as e:
                if device_id in self.devices:
                    # 静默处理接收错误
                    pass
                break
        
        print(f"接收线程结束: {device_id}")
    
    def send_message(self, device_index, message):
        """发送消息到指定设备"""
        try:
            # 查找指定索引的设备
            target_device_id = None
            for device_id, device_info in self.devices.items():
                if device_info['index'] == device_index:
                    target_device_id = device_id
                    break
            
            if target_device_id and target_device_id in self.device_handles:
                handle_info = self.device_handles[target_device_id]
                device_info = self.devices[target_device_id]
                
                # 发送数据
                if isinstance(message, str):
                    message = message.encode('utf-8')
                
                print(f"准备发送到 {device_info['name']} (接口 {device_info.get('interface', 'unknown')}): {message}")
                
                # 使用pyusb发送数据
                bytes_written = handle_info['ep_out'].write(message)
                print(f"消息已发送到 {device_info['name']}: {message} (写入 {bytes_written} 字节)")
                return True
            else:
                print(f"设备 {device_index} 未连接，可用设备: {list(self.devices.keys())}")
                self.error_occurred.emit(f"设备 {device_index} 未连接")
                return False
                
        except Exception as e:
            print(f"发送消息异常: {e}")
            self.error_occurred.emit(f"发送消息失败: {str(e)}")
            return False
    
    def get_connected_devices(self):
        """获取已连接的设备列表"""
        return [device_info['name'] for device_info in self.devices.values()]
    
    def is_device_connected(self, device_index):
        """检查指定设备是否已连接"""
        return any(device_info['index'] == device_index for device_info in self.devices.values())
    
    def is_device_readonly(self, device_index):
        """检查指定设备是否为只读接口"""
        for device_id, device_info in self.devices.items():
            if device_info['index'] == device_index:
                if device_id in self.device_handles:
                    handle_info = self.device_handles[device_id]
                    return handle_info.get('readonly', False) or handle_info['ep_out'] is None
        return False
    
    def get_device_capabilities(self, device_index):
        """获取设备的详细能力信息"""
        for device_id, device_info in self.devices.items():
            if device_info['index'] == device_index:
                if device_id in self.device_handles:
                    handle_info = self.device_handles[device_id]
                    capabilities = {
                        'name': device_info['name'],
                        'interface': device_info.get('interface', 'unknown'),
                        'connected': True,
                        'readonly': handle_info.get('readonly', False),
                        'can_send': handle_info['ep_out'] is not None and not handle_info.get('readonly', False),
                        'can_receive': handle_info['ep_in'] is not None,
                        'description': ''
                    }
                    
                    if capabilities['can_send'] and capabilities['can_receive']:
                        capabilities['description'] = "支持发送和接收"
                    elif capabilities['can_receive']:
                        capabilities['description'] = "只读模式 - 仅支持接收"
                    else:
                        capabilities['description'] = "无功能"
                    
                    return capabilities
        return None
    
    def get_device_info(self):
        """获取所有设备的详细信息"""
        device_info = {}
        for device_id, info in self.devices.items():
            device_info[info['index']] = {
                'name': info['name'],
                'id': device_id,
                'connected': True
            }
        return device_info
    
    def scan_all_devices(self):
        """扫描所有USB设备"""
        try:
            all_devices = list(usb.core.find(find_all=True, backend=self.backend))
            device_list = []
            
            for device in all_devices:
                try:
                    vid = device.idVendor
                    pid = device.idProduct
                    device_info = {
                        'vid': f"0x{vid:04X}",
                        'pid': f"0x{pid:04X}",
                        'bus': device.bus,
                        'address': device.address,
                        'is_target': (vid == self.vid and pid == self.pid)
                    }
                    device_list.append(device_info)
                except:
                    pass
            
            return device_list
        except Exception as e:
            return []
    
    def check_device_driver(self):
        """检查设备驱动状态"""
        try:
            import subprocess
            import re
            
            # 使用Windows命令检查设备状态
            result = subprocess.run(['devcon', 'findall', '*USB*'], 
                                  capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if f"{self.vid:04X}" in line and f"{self.pid:04X}" in line:
                        if "running" in line.lower():
                            return "驱动正常"
                        elif "stopped" in line.lower():
                            return "驱动已停止"
                        elif "error" in line.lower():
                            return "驱动错误"
                return "设备未找到"
            else:
                return "无法检查驱动状态"
        except Exception as e:
            return f"驱动检查失败: {e}"
    
    def cleanup(self):
        """清理资源"""
        self.stop_device_monitoring()
        
        # 关闭所有设备句柄
        for device_id in list(self.device_handles.keys()):
            try:
                # 释放USB设备
                if device_id in self.device_handles:
                    handle_info = self.device_handles[device_id]
                    usb.util.dispose_resources(handle_info['device'])
            except:
                pass
        
        self.device_handles.clear()
        self.devices.clear() 