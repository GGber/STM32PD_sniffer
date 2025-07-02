# usb_device.py
import usb.backend.libusb1
import os
import usb.core
import usb.util
import usb1

class USBDeviceManager:
    def __init__(self):
        self.device_list = []
        dll_path = os.path.join(os.path.dirname(__file__), "libusb-1.0.dll")
        self.dll_path = os.path.join(os.path.dirname(__file__), "libusb-1.0.dll")
        self.backend = usb.backend.libusb1.get_backend(find_library=lambda x: self.dll_path)

    def list_devices(self):
        self.device_list = list(usb.core.find(find_all=True, backend=self.backend))
        result = []

        for i, dev in enumerate(self.device_list):
            try:
                manufacturer = usb.util.get_string(dev, dev.iManufacturer)
                product = usb.util.get_string(dev, dev.iProduct)
            except Exception as e:
                manufacturer = product = "<无法访问>"
                print(f"[警告] 无法读取设备描述符 {hex(dev.idVendor)}:{hex(dev.idProduct)}: {e}")

            display_str = f"[{i}] {hex(dev.idVendor)}:{hex(dev.idProduct)} - {manufacturer} {product}"
            result.append(display_str)

        return result


    def open_device_by_index(self, index):
        if index >= len(self.device_list):
            raise IndexError("设备索引超出范围")

        target = self.device_list[index]
        vid = target.idVendor
        pid = target.idProduct

        self.context = usb1.USBContext()
        self.handle = self.context.openByVendorIDAndProductID(
            vid, pid,
            skip_on_error=True
        )

        if self.handle is None:
            raise ValueError("无法打开设备")

        self.handle.claimInterface(self.interface)
        print(f"已打开设备 VID:PID = {hex(vid)}:{hex(pid)}")

    def send(self, data: bytes):
        if self.handle is None:
            raise RuntimeError("USB设备未打开")
        self.handle.bulkWrite(self.out_ep, data)
        print(f"发送: {data}")

    def receive(self, length=64):
        if self.handle is None:
            raise RuntimeError("USB设备未打开")
        data = self.handle.bulkRead(self.in_ep, length)
        print(f"接收: {data}")
        return data

    def close(self):
        if self.handle:
            self.handle.releaseInterface(self.interface)
            self.handle.close()
        if self.context:
            self.context.close()
        print("USB设备已关闭")
