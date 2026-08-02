def crc16(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc

for payload in [b"firmware_v1.0", b"firmware_v1.1", b"config.bin"]:
    print(payload.decode(), f"{crc16(payload):04X}")
