_4b5b_table = {
    0x1E: 0x0, 0x09: 0x1, 0x14: 0x2, 0x15: 0x3,
    0x0A: 0x4, 0x0B: 0x5, 0x0E: 0x6, 0x0F: 0x7,
    0x12: 0x8, 0x13: 0x9, 0x16: 0xA, 0x17: 0xB,
    0x1A: 0xC, 0x1B: 0xD, 0x1C: 0xE, 0x1D: 0xF,
}

def parse_pd_data(data: bytes) -> str:

    sop = data[:4]
    data_field = data[4:]
    nibbles = []
    for b in data_field:
        code = b & 0x1F
        if code in _4b5b_table:
            nibbles.append(_4b5b_table[code])
    # 每两个nibble拼成一个字节（低4位在前，高4位在后）
    pd_bytes = bytearray()
    for i in range(0, len(nibbles)-1, 2):
        pd_bytes.append((nibbles[i+1] << 4) | nibbles[i])
    if len(nibbles) % 2 == 1:
        pd_bytes.append(nibbles[-1])  # 最后一个nibble单独补齐
    # 拼回完整协议帧
    data = sop + pd_bytes
    if len(data) < 6:
        return f"数据长度不足，原始: {data.hex(' ').upper()}"
    header = data[4:6]
    header_val = int.from_bytes(header, 'little')

    # SOP*类型识别
    sop_map = {
        b'\x18\x18\x18\x11': "SOP",
        b'\x18\x18\x06\x06': "SOP'",
        b'\x18\x18\x05\x05': "SOP''",
        b'\x12\x12\x12\x13': "Hard Reset",
        b'\x19\x19\x19\x1B': "Cable Reset",
        b'\xFF\xFF\xFF\xFF': "EOP"
    }
    sop_type = sop_map.get(bytes(sop), "未知/自定义SOP*")

    # 头部字段解析（PD2.0/3.2通用）
    msg_type = header_val & 0x1F  # 0-4bit
    port_data_role = (header_val >> 5) & 0x1  # 5bit
    spec_revision = (header_val >> 6) & 0x3   # 6-7bit
    port_power_role = (header_val >> 8) & 0x1 # 8bit
    msg_id = (header_val >> 9) & 0x7          # 9-11bit
    num_data_obj = (header_val >> 12) & 0x7   # 12-14bit
    ext = (header_val >> 15) & 0x1            # 15bit (PD3.0/3.2扩展)

    # 字段含义映射
    port_data_role_map = ["UFP", "DFP"]
    port_power_role_map = ["Sink", "Source"]
    spec_revision_map = ["1.0", "2.0", "3.0/3.2"]

    # 判断消息类别
    if num_data_obj == 0:
        msg_class = "Control Message"
    else:
        msg_class = "Data Message"

    # 计算data区长度
    data_len = num_data_obj * 4
    data_bytes = data[6:6+data_len] if data_len > 0 else b''
    crc = data[6+data_len:6+data_len+4]
    eop = data[6+data_len+4:6+data_len+5]

    result = []
    result.append(f"{sop_type}")
    result.append(f"-{msg_class}")
    result.append(f"-{port_power_role_map[port_power_role]}")
    result.append(f"-{spec_revision_map[spec_revision] if spec_revision < len(spec_revision_map) else '未知'}")
    result.append(f"-{port_data_role_map[port_data_role]}")
    result.append(f"-ID:{msg_id:d}")

    if num_data_obj == 0:
        # 解析Control Message
        ctrl_detail = parse_pd_control_message(msg_type)
        result.append(f"    {ctrl_detail}")
    else:
        # 进一步解析Data区
        data_detail = parse_pd_data_object(msg_type, data_bytes)
        result.append(f"    {data_detail}")

    result.append(f"CRC: {crc.hex(' ').upper()}")
    result.append(f"EOP: {eop.hex(' ').upper()}")
    return '\n'.join(result)

def parse_pd_control_message(msg_type: int) -> str:
    """
    解析PD Control Message类型，返回详细含义。
    """
    ctrl_map = {
        0: "Reserved",
        1: "GoodCRC：确认收到数据包",
        2: "GotoMin：请求降到最小电流/功率",
        3: "Accept：接受前一条消息",
        4: "Reject：拒绝前一条消息",
        5: "Ping：Ping信号",
        6: "PS_RDY：电源准备就绪",
        7: "Get_Source_Cap：请求源能力",
        8: "Get_Sink_Cap：请求受电能力",
        9: "DR_Swap：数据角色切换",
        10: "PR_Swap：电源角色切换",
        11: "VCONN_Swap：VCONN切换",
        12: "Wait：暂时无法处理",
        13: "Soft_Reset：软复位",
        14: "Not_Supported：不支持",
        15: "Get_Source_Cap_Ext：请求扩展源能力"
    }
    return ctrl_map.get(msg_type, "未知Control Message")

def parse_pd_data_object(msg_type: int, data_bytes: bytes) -> str:
    """
    针对不同msg_type解析不同的Data Object内容。
    支持Source Capabilities、Request、BIST、Sink Capabilities、Vendor Defined等常见类型。
    """
    if not data_bytes:
        return "(无Data Object)"
    # Source Capabilities
    if msg_type == 1:
        return parse_source_capabilities(data_bytes)
    # Request
    elif msg_type == 2:
        return parse_request_data_object(data_bytes)
    # BIST
    elif msg_type == 3:
        return parse_bist_data_object(data_bytes)
    # Sink Capabilities
    elif msg_type == 4:
        return parse_sink_capabilities(data_bytes)
    # Battery Status
    elif msg_type == 5:
        return parse_battery_status(data_bytes)
    # Alert
    elif msg_type == 6:
        return parse_alert_data_object(data_bytes)
    # Get Country Info
    elif msg_type == 7:
        return parse_country_info(data_bytes)
    # Enter_USB
    elif msg_type == 8:
        return parse_enter_usb(data_bytes)
    # Vendor Defined
    elif msg_type == 15:
        return parse_vendor_defined(data_bytes)
    else:
        return "(暂未实现详细解析)"

def parse_source_capabilities(data_bytes: bytes) -> str:
    """解析Source Capabilities Data Objects"""
    result = []
    count = len(data_bytes) // 4
    for i in range(count):
        pdo = int.from_bytes(data_bytes[i*4:(i+1)*4], 'little')
        pdo_type = (pdo >> 30) & 0x3
        if pdo_type == 0:
            # Fixed Supply PDO
            voltage = ((pdo >> 10) & 0x3FF) * 50  # mV
            current = (pdo & 0x3FF) * 10          # mA
            result.append(f"  PDO[{i}]: 固定供电 {voltage/1000:.2f}V {current}mA")
        elif pdo_type == 1:
            # Battery Supply PDO
            max_voltage = ((pdo >> 20) & 0x3FF) * 50
            min_voltage = ((pdo >> 10) & 0x3FF) * 50
            max_power = (pdo & 0x3FF) * 250
            result.append(f"  PDO[{i}]: 电池供电 {min_voltage/1000:.2f}-{max_voltage/1000:.2f}V {max_power/1000:.2f}W")
        elif pdo_type == 2:
            # Variable Supply PDO
            max_voltage = ((pdo >> 20) & 0x3FF) * 50
            min_voltage = ((pdo >> 10) & 0x3FF) * 50
            max_current = (pdo & 0x3FF) * 10
            result.append(f"  PDO[{i}]: 可变供电 {min_voltage/1000:.2f}-{max_voltage/1000:.2f}V {max_current}mA")
        else:
            result.append(f"  PDO[{i}]: 未知/自定义类型")
    return '\n'.join(result)

def parse_request_data_object(data_bytes: bytes) -> str:
    """解析Request Data Object (RDO)"""
    if len(data_bytes) < 4:
        return "(RDO长度不足)"
    rdo = int.from_bytes(data_bytes[:4], 'little')
    obj_pos = (rdo >> 28) & 0x7
    giveback = (rdo >> 27) & 0x1
    capability_mismatch = (rdo >> 26) & 0x1
    usb_comm_cap = (rdo >> 25) & 0x1
    no_usb_suspend = (rdo >> 24) & 0x1
    op_current = (rdo >> 10) & 0x3FF
    max_current = rdo & 0x3FF
    return (f"  Request: Object ={obj_pos}, GiveBack={giveback}, "
            f"CapabilityMismatch={capability_mismatch}, USBCommCap={usb_comm_cap}, "
            f"NoUSBSuspend={no_usb_suspend}, "
            f"OpCurrent={op_current*10}mA, MaxCurrent={max_current*10}mA")

def parse_sink_capabilities(data_bytes: bytes) -> str:
    """解析Sink Capabilities Data Objects"""
    result = []
    count = len(data_bytes) // 4
    for i in range(count):
        pdo = int.from_bytes(data_bytes[i*4:(i+1)*4], 'little')
        pdo_type = (pdo >> 30) & 0x3
        if pdo_type == 0:
            # Fixed Supply PDO
            voltage = ((pdo >> 10) & 0x3FF) * 50  # mV
            current = (pdo & 0x3FF) * 10          # mA
            result.append(f"  Sink PDO[{i}]: 固定供电 {voltage/1000:.2f}V {current}mA")
        elif pdo_type == 1:
            # Battery Supply PDO
            max_voltage = ((pdo >> 20) & 0x3FF) * 50
            min_voltage = ((pdo >> 10) & 0x3FF) * 50
            max_power = (pdo & 0x3FF) * 250
            result.append(f"  Sink PDO[{i}]: 电池供电 {min_voltage/1000:.2f}-{max_voltage/1000:.2f}V {max_power/1000:.2f}W")
        elif pdo_type == 2:
            # Variable Supply PDO
            max_voltage = ((pdo >> 20) & 0x3FF) * 50
            min_voltage = ((pdo >> 10) & 0x3FF) * 50
            max_current = (pdo & 0x3FF) * 10
            result.append(f"  Sink PDO[{i}]: 可变供电 {min_voltage/1000:.2f}-{max_voltage/1000:.2f}V {max_current}mA")
        else:
            result.append(f"  Sink PDO[{i}]: 未知/自定义类型")
    return '\n'.join(result)

def parse_vendor_defined(data_bytes: bytes) -> str:
    """解析Vendor Defined Message (VDM)"""
    vdm_header = int.from_bytes(data_bytes[:4], 'little')
    svid = vdm_header & 0xFFFF
    vdm_type = (vdm_header >> 15) & 0x1
    cmd_type = (vdm_header >> 6) & 0x3
    cmd = (vdm_header >> 8) & 0x1F
    return (f"  VDM: SVID=0x{svid:04X}, VDMType={vdm_type}, CmdType={cmd_type}, Cmd={cmd}")

def parse_bist_data_object(data_bytes: bytes) -> str:
    return f"  BIST: {data_bytes.hex(' ').upper()}"

def parse_battery_status(data_bytes: bytes) -> str:
    return f"  Battery Status: {data_bytes.hex(' ').upper()}"

def parse_alert_data_object(data_bytes: bytes) -> str:
    return f"  Alert: {data_bytes.hex(' ').upper()}"

def parse_country_info(data_bytes: bytes) -> str:
    return f"  Country Info: {data_bytes.hex(' ').upper()}"

def parse_enter_usb(data_bytes: bytes) -> str:
    return f"  Enter_USB: {data_bytes.hex(' ').upper()}" 