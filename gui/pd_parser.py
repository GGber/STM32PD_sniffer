_4b5b_table = {
    0x1E: 0x0, 0x09: 0x1, 0x14: 0x2, 0x15: 0x3,
    0x0A: 0x4, 0x0B: 0x5, 0x0E: 0x6, 0x0F: 0x7,
    0x12: 0x8, 0x13: 0x9, 0x16: 0xA, 0x17: 0xB,
    0x1A: 0xC, 0x1B: 0xD, 0x1C: 0xE, 0x1D: 0xF,
}

def parse_pd_data(packet: bytes) -> dict:
    result = {
        "timestamp": None,
        "sop_type": None,
        "msg_type": None,
        "power_role": None,
        "spec_revision": None,
        "data_role": None,
        "msg_id": None,
        "raw_hex": None,
        "header_data_hex": None,
        "detail": None,
        "error": False,
        "error_msg": ""
    }
    print(f"[PD解析] 接收到原始数据: {packet.hex(' ').upper()}")
    if len(packet) < 6:
        result["error"] = True
        result["error_msg"] = f"数据包长度不足，原始: {packet.hex(' ').upper()}"
        result["raw_hex"] = packet.hex(' ').upper()
        return result
    func_code = packet[0]
    if func_code != 0xAA:
        result["error"] = True
        result["error_msg"] = f"非PD包，功能码: 0x{func_code:02X}"
        result["raw_hex"] = packet.hex(' ').upper()
        return result
    timestamp = int.from_bytes(packet[1:5], 'little')  # ms
    pd_raw = packet[5:]
    sop = pd_raw[:4]
    data_field = pd_raw[4:]
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
        pd_bytes.append((nibbles[-1] << 4))  # 最后一个nibble单独补齐
    # 拼回完整协议帧
    data = sop + pd_bytes
    result["raw_hex"] = data.hex(' ').upper()
    result["timestamp"] = timestamp
    if len(data) < 6:
        result["error"] = True
        result["error_msg"] = f"数据长度不足，原始: {result['raw_hex']}"
        return result
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
    result["sop_type"] = sop_type
    # 头部字段解析
    msg_type = header_val & 0x1F
    port_data_role = (header_val >> 5) & 0x1
    spec_revision = (header_val >> 6) & 0x3
    port_power_role = (header_val >> 8) & 0x1
    msg_id = (header_val >> 9) & 0x7
    num_data_obj = (header_val >> 12) & 0x7
    ext = (header_val >> 15) & 0x1
    port_data_role_map = ["UFP", "DFP"]
    port_power_role_map = ["Sink", "Source"]
    spec_revision_map = ["1.0", "2.0", "3.0/3.2"]
    result["power_role"] = port_power_role_map[port_power_role]
    result["spec_revision"] = spec_revision_map[spec_revision] if spec_revision < len(spec_revision_map) else '未知'
    result["data_role"] = port_data_role_map[port_data_role]
    result["msg_id"] = msg_id
    # header+data区原始数据
    data_len = num_data_obj * 4
    header_data = data[4:6+data_len] if len(data) >= 6+data_len else data[4:]
    result["header_data_hex"] = header_data.hex(' ').upper()
    # 消息类型判断与解析
    if num_data_obj == 0:
        ctrl_type = parse_pd_control_message(msg_type)
        result["msg_type"] = ctrl_type
        result["detail"] = ctrl_type
    elif ext == 1:
        ext_type = parse_ext_message(msg_type, data[6:6+num_data_obj*4] if num_data_obj > 0 else b'')
        result["msg_type"] = ext_type
        result["detail"] = ext_type
    else:
        data_type = parse_pd_data_object(msg_type, data[6:6+num_data_obj*4] if num_data_obj > 0 else b'')
        result["msg_type"] = data_type
        result["detail"] = data_type
    return result

def parse_pd_control_message(msg_type: int) -> str:
    """
    解析PD Control Message类型，返回详细含义。
    完整支持0-23类型。
    """
    ctrl_map = {
        0: "Reserved",
        1: "GoodCRC",
        2: "GotoMin",
        3: "Accept",
        4: "Reject",
        5: "Ping",
        6: "PS_RDY",
        7: "Get_Source_Cap",
        8: "Get_Sink_Cap",
        9: "DR_Swap",
        10: "PR_Swap",
        11: "VCONN_Swap",
        12: "Wait",
        13: "Soft_Reset",
        14: "Data_Reset",
        15: "Data_Reset_Complete",
        16: "Not_Supported",
        17: "Get_Source_Cap_Extended",
        18: "Get_Status",
        19: "FR_Swap",
        20: "Get_PPS_Status",
        21: "Get_Country_Codes",
        22: "Get_Sink_Cap_Extended",
        23: "Get_Source_Info",
        24: "Get_Revision"
    }
    return ctrl_map.get(msg_type, "Reserved")

def parse_pd_data_object(msg_type: int, data_bytes: bytes) -> str:
    """
    只处理标准Data Message（不处理ext/obj判断）。
    返回类型名由data_map决定。
    """
    data_map = {
        0: "Reserved",
        1: "Source Capabilities",
        2: "Request",
        3: "BIST",
        4: "Sink Capabilities",
        5: "Battery Status",
        6: "Alert",
        7: "Country Info",
        8: "Enter_USB",
        9: "EPR_Request",
        10: "EPR_Mode",
        11: "Source_Info",
        12: "Revision",
        13: "Reserved",
        14: "Reserved",
        15: "Vendor Defined"
    }
    if not data_bytes:
        return data_map.get(msg_type, f"Data Message({msg_type})")
    # 具体内容解析（如需详细内容可扩展）
    if msg_type == 1:
        return data_map[1]
    elif msg_type == 2:
        return data_map[2]
    elif msg_type == 3:
        return data_map[3]
    elif msg_type == 4:
        return data_map[4]
    elif msg_type == 5:
        return data_map[5]
    elif msg_type == 6:
        return data_map[6]
    elif msg_type == 7:
        return data_map[7]
    elif msg_type == 8:
        return data_map[8]
    elif msg_type == 9:
        return data_map[9]
    elif msg_type == 10:
        return data_map[10]
    elif msg_type == 11:
        return data_map[11]
    elif msg_type == 12:
        return data_map[12]
    elif msg_type == 13:
        return data_map[13]
    elif msg_type == 14:
        return data_map[14]
    elif msg_type == 15:
        return data_map[15]
    else:
        return f"Data Message({msg_type})"

def parse_ext_message(msg_type: int, data_bytes: bytes) -> str:
    """
    解析PD Extended Message (EXT message)。
    参考PD3.0/3.1/3.2规范。
    """
    ext_map = {
        0: "Reserved",
        1: "Source_Capabilities_Extended",
        2: "Status",
        3: "Get_Battery_Cap",
        4: "Get_Battery_Status",
        5: "Battery_Capabilities",
        6: "Get_Manufacturer_Info",
        7: "Manufacturer_Info",
        8: "Security_Request",
        9: "Security_Response",
        10: "Firmware_Update_Request",
        11: "Firmware_Update_Response",
        12: "PPS_Status",
        13: "Country_Info",
        14: "Country_Codes",
        15: "Sink_Capabilities_Extended",
        16: "Extended_Control",
        17: "EPR_Source_Capabilities",
        18: "EPR_Sink_Capabilities",
        30: "Vendor_Defined_Extended",
        31: "Reserved"
    }
    ext_type = ext_map.get(msg_type, "Reserved")
    return ext_type

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