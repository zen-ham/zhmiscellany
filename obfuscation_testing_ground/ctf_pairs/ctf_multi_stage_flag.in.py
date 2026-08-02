import base64

def pack(flag, key):
    xored = bytes(b ^ key for b in flag.encode())
    return base64.b64encode(xored[::-1]).decode()

def unpack(blob, key):
    raw = base64.b64decode(blob)[::-1]
    return bytes(b ^ key for b in raw).decode()

KEY = 0x5A
blob = pack("CTF{multi_stage_decode}", KEY)
print(blob)
print(unpack(blob, KEY))
