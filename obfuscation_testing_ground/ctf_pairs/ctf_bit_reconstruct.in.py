def reconstruct(parts):
    value = 0
    for shift, byte in parts:
        value |= byte << shift
    return value

parts = [(0, 0x6C), (8, 0x6F), (16, 0x6F), (24, 0x6C)]
secret = reconstruct(parts)
print(hex(secret))
print(secret.to_bytes(4, "little").decode())
