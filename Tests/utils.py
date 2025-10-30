import struct

def to_dict(payload: bytes):
    if len(payload) != 64:
        raise ValueError('Payload must be 64 bytes')
    else:
        package_id = struct.unpack('<H', payload[1:3])[0]
        byte6 = struct.unpack('<B', payload[5:6])[0]
        flag_valid = byte6 & 0x1
        flag_pos = (byte6 & 0x10) >> 4
        flag_neg = (byte6 & 0x8) >> 3
        count_pos = int.from_bytes(payload[58:61], byteorder="little")
        count_neg = int.from_bytes(payload[61:63], byteorder="little")
        count_hundred = int.from_bytes(payload[6:10], byteorder="little")
        flag_parity = byte6 & 0b00100000

        result = {
            "package_id": package_id,
            "flag_valid": flag_valid,
            "flag_neg": flag_neg,
            "flag_pos": flag_pos,
            "count_neg": count_neg,
            "count_pos": count_pos,
            "count_hundred" : count_hundred,
            "flag_parity": flag_parity
        }
    return result

def packet_callback(packet):
    if packet.haslayer("Raw"):
        payload = bytes(packet["Raw"].load)[42:]
        try:
            result = to_dict(payload)
            if result['flag_valid'] == 1 and result['flag_pos'] == 1:
               #print(result)
                pass
        except Exception as e:
            pass
