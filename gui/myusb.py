import logging
import time
import sys  # 添加这一行导入sys模块
from contextlib import contextmanager
from typing import Optional, List, Tuple, Dict, Union, Any
import usb.core
import usb.util

logger = logging.getLogger(__name__)

class USBError(Exception):
    """USB操作相关的异常基类"""
    pass

class USBConnectionError(USBError):
    """USB连接错误"""
    pass

class USBTransferError(USBError):
    """USB数据传输错误"""
    pass

class USBDeviceManager:
    """
    USB设备管理器，用于处理USB设备的连接、数据传输等功能。
    支持多接口操作，自动重连，详细的错误报告。
    """
    
    def __init__(self, vid: int, pid: int, timeout: int = 1000, 
                 retry_count: int = 3, retry_delay: float = 0.5, 
                 auto_reconnect: bool = True):
        """
        初始化USB设备管理器
        
        Args:
            vid: 厂商ID
            pid: 产品ID
            timeout: USB操作超时时间(毫秒)
            retry_count: 操作失败时的重试次数
            retry_delay: 重试之间的延迟(秒)
            auto_reconnect: 在操作失败时是否自动尝试重新连接设备
        """
        self.vid = vid
        self.pid = pid
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.auto_reconnect = auto_reconnect
        
        # 设备和接口状态
        self.device = None
        self.interfaces = {}  # {接口索引: (接口, 输入端点, 输出端点)}
        self.connected = False
        self.last_error = None
        
        # 接口配置信息缓存
        self._interface_cache = {}  # {接口索引: (接口号, 输入端点地址, 输出端点地址)}
        
        logger.debug(f"USBDeviceManager初始化: VID=0x{vid:04X}, PID=0x{pid:04X}")
    
    def __del__(self):
        """析构函数，确保在对象销毁时释放资源"""
        self.disconnect()
    
    @contextmanager
    def auto_recover(self, interface_index=None):
        """
        上下文管理器，用于在操作失败时自动恢复连接
        
        Args:
            interface_index: 操作的接口索引，如果为None则表示不针对特定接口
            
        Yields:
            None
        """
        try:
            yield
        except (usb.core.USBError, USBError) as e:
            self.last_error = str(e)
            logger.warning(f"USB操作错误: {e}")
            
            if self.auto_reconnect:
                logger.info("尝试重新连接设备...")
                self.disconnect()
                time.sleep(0.5)
                try:
                    self.connect()
                    if interface_index is not None:
                        self.claim_interface(interface_index)
                    logger.info("重新连接成功")
                except Exception as reconnect_error:
                    logger.error(f"重新连接失败: {reconnect_error}")
                    raise USBConnectionError(f"重新连接失败: {reconnect_error}") from e
            else:
                raise
    
    def connect(self) -> bool:
        """
        连接到USB设备
        """
        if self.connected and self.device:
            return True
            
        try:
            # 尝试显式导入可用的后端
            import usb.backend.libusb1 as libusb1
            import os
            
            # Windows系统下尝试查找libusb DLL
            backend = None
            if os.name == 'nt':
                # 尝试在常见位置查找DLL
                dll_paths = [
                    # 当前目录
                    './libusb-1.0.dll',
                    # Python安装目录下的DLL
                    os.path.join(os.path.dirname(sys.executable), 'libusb-1.0.dll'),
                    # 系统路径
                    'libusb-1.0.dll'
                ]
                
                for path in dll_paths:
                    if os.path.exists(path):
                        backend = libusb1.get_backend(find_library=lambda x: path)
                        logger.debug(f"找到libusb DLL: {path}")
                        break
            else:
                # Linux/macOS可以自动查找
                backend = libusb1.get_backend()
            
            if backend is None:
                logger.warning("无法找到libusb后端，尝试不指定后端")
            
            # 查找设备
            self.device = usb.core.find(idVendor=self.vid, idProduct=self.pid, backend=backend)

            if self.device is None:
                logger.error(f"未找到设备: VID=0x{self.vid:04X}, PID=0x{self.pid:04X}")
                self.connected = False
                raise USBConnectionError(f"未找到设备: VID=0x{self.vid:04X}, PID=0x{self.pid:04X}")
            
            # 获取设备信息
            try:
                self.manufacturer = usb.util.get_string(self.device, self.device.iManufacturer)
                self.product = usb.util.get_string(self.device, self.device.iProduct)
                self.serial_number = usb.util.get_string(self.device, self.device.iSerialNumber)
                logger.info(f"设备信息: {self.manufacturer} {self.product} (SN: {self.serial_number})")
            except:
                logger.debug("无法获取完整设备信息")
            
            # 检查当前配置
            if self.device.get_active_configuration() is None:
                logger.debug("设置默认配置")
                self.device.set_configuration()
            
            # 重置所有接口状态
            self.interfaces = {}
            self._interface_cache = {}
            
            self.connected = True
            logger.info(f"成功连接到设备: VID=0x{self.vid:04X}, PID=0x{self.pid:04X}")
            return True
            
        except usb.core.USBError as e:
            self.device = None
            self.connected = False
            self.last_error = str(e)
            logger.error(f"连接设备失败: {e}")
            raise USBConnectionError(f"连接设备失败: {e}") from e
    
    def disconnect(self) -> bool:
        """
        断开与USB设备的连接，释放所有资源
        
        Returns:
            bool: 断开操作是否成功
        """
        if not self.connected or self.device is None:
            self.connected = False
            self.device = None
            self.interfaces = {}
            return True
        
        try:
            # 释放所有接口
            for interface_index, (interface, _, _) in self.interfaces.items():
                try:
                    logger.debug(f"释放接口 {interface_index}")
                    usb.util.release_interface(self.device, interface)
                except Exception as e:
                    logger.debug(f"释放接口 {interface_index} 失败: {e}")
            
            # 重置设备（可选）
            try:
                self.device.reset()
            except Exception as e:
                logger.debug(f"重置设备失败: {e}")
            
            # 释放设备资源
            usb.util.dispose_resources(self.device)
            
        except Exception as e:
            logger.warning(f"断开连接过程中出现错误: {e}")
        
        # 无论是否成功都重置状态
        self.device = None
        self.connected = False
        self.interfaces = {}
        logger.info("设备已断开连接")
        return True
    
    def claim_interface(self, interface_index: int) -> bool:
        """
        声明一个接口用于数据传输
        
        Args:
            interface_index: 接口索引
            
        Returns:
            bool: 操作是否成功
            
        Raises:
            USBConnectionError: 如果未连接设备或接口操作失败
        """
        if not self.connected or self.device is None:
            logger.error("尝试声明接口，但设备未连接")
            raise USBConnectionError("设备未连接")
        
        # 检查接口是否已经被声明
        if interface_index in self.interfaces:
            return True
        
        try:
            # 查找接口
            cfg = self.device.get_active_configuration()
            
            # 检查缓存
            if interface_index in self._interface_cache:
                intf_num, in_ep_addr, out_ep_addr = self._interface_cache[interface_index]
                logger.debug(f"使用缓存的接口信息: 接口{intf_num}, IN=0x{in_ep_addr:02X}, OUT=0x{out_ep_addr:02X}")
                
                intf = usb.util.find_descriptor(
                    cfg,
                    bInterfaceNumber=intf_num
                )
            else:
                # 没有缓存，找到接口号最小的未使用接口
                used_interfaces = set(i[0].bInterfaceNumber for i in self.interfaces.values())
                available_interfaces = []
                
                for i in range(cfg.bNumInterfaces):
                    intf = usb.util.find_descriptor(
                        cfg, 
                        bInterfaceClass=usb.CLASS_VENDOR_SPEC,
                        bInterfaceNumber=i
                    )
                    if intf and intf.bInterfaceNumber not in used_interfaces:
                        available_interfaces.append(intf)
                
                if not available_interfaces:
                    logger.error("没有可用的接口")
                    raise USBConnectionError("没有可用的接口")
                
                # 按接口号排序，选择最小的
                available_interfaces.sort(key=lambda x: x.bInterfaceNumber)
                intf = available_interfaces[min(interface_index, len(available_interfaces)-1)]
                intf_num = intf.bInterfaceNumber
            
            # 查找端点
            in_ep = None
            out_ep = None
            
            for ep in intf:
                if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN:
                    in_ep = ep
                else:
                    out_ep = ep
            
            if not in_ep or not out_ep:
                logger.error(f"接口 {intf_num} 未找到所需的端点")
                raise USBConnectionError(f"接口 {intf_num} 未找到所需的端点")
            
            # 尝试声明接口
            if self.device.is_kernel_driver_active(intf_num):
                logger.debug(f"接口 {intf_num} 正被内核驱动使用，尝试分离")
                self.device.detach_kernel_driver(intf_num)
            
            usb.util.claim_interface(self.device, intf_num)
            
            # 缓存接口信息
            self._interface_cache[interface_index] = (intf_num, in_ep.bEndpointAddress, out_ep.bEndpointAddress)
            
            # 保存接口和端点
            self.interfaces[interface_index] = (intf, in_ep, out_ep)
            logger.info(f"成功声明接口 {intf_num} (索引 {interface_index})")
            return True
            
        except usb.core.USBError as e:
            self.last_error = str(e)
            logger.error(f"声明接口失败: {e}")
            raise USBConnectionError(f"声明接口失败: {e}") from e
    
    def send(self, data: bytes, interface_index: int = 0) -> int:
        """
        通过指定接口发送数据
        
        Args:
            data: 要发送的数据
            interface_index: 接口索引
            
        Returns:
            int: 发送的字节数
            
        Raises:
            USBConnectionError: 如果设备未连接
            USBTransferError: 如果发送失败
        """
        if not self.connected or self.device is None:
            logger.error("尝试发送数据，但设备未连接")
            raise USBConnectionError("设备未连接")
        
        # 确保接口已声明
        if interface_index not in self.interfaces:
            logger.debug(f"接口 {interface_index} 未声明，尝试自动声明")
            self.claim_interface(interface_index)
        
        _, _, out_ep = self.interfaces[interface_index]
        
        for attempt in range(self.retry_count + 1):
            try:
                with self.auto_recover(interface_index):
                    bytes_sent = self.device.write(out_ep.bEndpointAddress, data, timeout=self.timeout)
                    logger.debug(f"发送到接口 {interface_index}: {bytes_sent} 字节")
                    return bytes_sent
            except Exception as e:
                if attempt < self.retry_count:
                    logger.warning(f"发送失败 (尝试 {attempt+1}/{self.retry_count}): {e}")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"发送失败，已达最大重试次数: {e}")
                    raise USBTransferError(f"发送失败: {e}") from e
    
    def receive(self, interface_index: int = 0, max_size: int = 64) -> bytes:
        """
        从指定接口接收数据
        
        Args:
            interface_index: 接口索引
            max_size: 接收缓冲区大小
            
        Returns:
            bytes: 接收到的数据
            
        Raises:
            USBConnectionError: 如果设备未连接
            USBTransferError: 如果接收失败
        """
        if not self.connected or self.device is None:
            logger.error("尝试接收数据，但设备未连接")
            raise USBConnectionError("设备未连接")
        
        # 确保接口已声明
        if interface_index not in self.interfaces:
            logger.debug(f"接口 {interface_index} 未声明，尝试自动声明")
            self.claim_interface(interface_index)
        
        _, in_ep, _ = self.interfaces[interface_index]
        
        for attempt in range(self.retry_count + 1):
            try:
                with self.auto_recover(interface_index):
                    data = self.device.read(in_ep.bEndpointAddress, max_size, timeout=self.timeout)
                    if data:
                        logger.debug(f"从接口 {interface_index} 接收: {len(data)} 字节")
                    return bytes(data)
            except usb.core.USBTimeoutError:
                # 超时通常表示没有数据可读，不是错误
                return b''
            except Exception as e:
                if attempt < self.retry_count and self.auto_reconnect:
                    logger.warning(f"接收失败 (尝试 {attempt+1}/{self.retry_count}): {e}")
                    time.sleep(self.retry_delay)
                else:
                    # 对于接收操作，某些错误可能只需要返回空数据而不是抛出异常
                    logger.debug(f"接收失败，已达最大重试次数: {e}")