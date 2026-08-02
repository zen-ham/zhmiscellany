"""
Small, realistic, benign "crackme / CTF" style programs -- each has some logic
worth hiding (a validation algorithm, a secret transform, a hidden flag), which
is exactly the kind of thing you'd point an obfuscator at. All are self-contained,
stdlib-only, deterministic, and print a result (so the harness can verify the
obfuscated version behaves identically).

These are intentionally toned-down teaching examples (license checks, XOR demos,
keygen-me's, a tiny VM) -- not tools for attacking real software.
"""
import textwrap

C = {}
def add(n, code): C[n] = textwrap.dedent(code).lstrip("\n")

add("license_key", '''
    def valid(key):
        if len(key) != 19 or key.count("-") != 3:
            return False
        parts = key.split("-")
        if any(len(p) != 4 for p in parts):
            return False
        body = key.replace("-", "")[:-2]
        want = sum(ord(c) for c in body) % 100
        try:
            got = int(parts[-1][-2:], 16)
        except ValueError:
            return False
        return want == got

    for k in ["ABCD-1234-EFGH-0041", "ZZZZ-9999-AAAA-0000", "PYTH-0N15-G00D-00FF"]:
        print(k, "VALID" if valid(k) else "INVALID")
''')

add("xor_cipher", '''
    def xor_bytes(data, key):
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

    SECRET = b"flag{x0r_15_n0t_encrypt10n}"
    KEY = b"obfuscate"
    cipher = xor_bytes(SECRET, KEY)
    recovered = xor_bytes(cipher, KEY)
    print(cipher.hex())
    print(recovered.decode())
''')

add("password_gate", '''
    import hashlib

    STORED = hashlib.sha256(b"S3cr3t-Adm1n!").hexdigest()

    def authenticate(pw):
        return hashlib.sha256(pw.encode()).hexdigest() == STORED

    for attempt in ["password", "admin", "S3cr3t-Adm1n!"]:
        print(attempt, "GRANTED" if authenticate(attempt) else "DENIED")
''')

add("serial_luhn", '''
    def luhn_ok(num):
        digits = [int(d) for d in num if d.isdigit()]
        checksum = 0
        for i, d in enumerate(reversed(digits)):
            if i % 2 == 1:
                d *= 2
                if d > 9:
                    d -= 9
            checksum += d
        return checksum % 10 == 0

    for s in ["4539578763621486", "1234567890123456", "79927398713"]:
        print(s, luhn_ok(s))
''')

add("caesar_decode", '''
    def shift(text, n):
        out = []
        for c in text:
            if c.isalpha():
                base = ord("A") if c.isupper() else ord("a")
                out.append(chr((ord(c) - base + n) % 26 + base))
            else:
                out.append(c)
        return "".join(out)

    ENC = "Wkh vhfuhw sdvvskudvh lv: FDHVDU"
    print(shift(ENC, -3))
''')

add("tiny_vm", '''
    def run(program):
        stack = []
        for op, arg in program:
            if op == "PUSH":
                stack.append(arg)
            elif op == "ADD":
                b = stack.pop(); a = stack.pop(); stack.append(a + b)
            elif op == "MUL":
                b = stack.pop(); a = stack.pop(); stack.append(a * b)
            elif op == "XOR":
                b = stack.pop(); a = stack.pop(); stack.append(a ^ b)
            elif op == "EMIT":
                return chr(stack.pop())
        return None

    prog = [("PUSH", 7), ("PUSH", 6), ("MUL", 0), ("PUSH", 65), ("ADD", 0),
            ("PUSH", 30), ("XOR", 0), ("EMIT", 0)]
    print(run(prog))
''')

add("keygen_verify", '''
    def keygen(user):
        h = 0x1505
        for c in user.encode():
            h = ((h << 5) + h + c) & 0xFFFFFFFF
        return f"{h:08X}"

    def verify(user, key):
        return keygen(user) == key

    cases = [("alice", "0AB3C1D2"), ("bob", keygen("bob")), ("root", keygen("root"))]
    for user, key in cases:
        print(user, key, verify(user, key))
''')

add("multi_stage_flag", '''
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
''')

add("constraint_solver", '''
    # the "flag" is the unique (a, b, c) satisfying these constraints
    def solve():
        for a in range(1, 10):
            for b in range(1, 10):
                for c in range(1, 10):
                    if a * 3 + b * 7 == 47 and a * b == 20 and a + b + c == 12:
                        return (a, b, c)
        return None

    print(solve())
''')

add("crc_checksum", '''
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
''')

add("bit_reconstruct", '''
    def reconstruct(parts):
        value = 0
        for shift, byte in parts:
            value |= byte << shift
        return value

    parts = [(0, 0x6C), (8, 0x6F), (16, 0x6F), (24, 0x6C)]
    secret = reconstruct(parts)
    print(hex(secret))
    print(secret.to_bytes(4, "little").decode())
''')

add("lcg_token", '''
    def lcg_stream(seed, n):
        x = seed
        out = []
        for _ in range(n):
            x = (1103515245 * x + 12345) & 0x7FFFFFFF
            out.append(x % 100)
        return out

    token = lcg_stream(0x1337, 6)
    print("-".join(f"{v:02d}" for v in token))
''')


if __name__ == "__main__":
    # quick self-check that each runs clean + deterministic
    from harness import check
    nbad = 0
    for name, code in C.items():
        ok, status, detail = check(code)
        flag = "ok " if ok else "BAD"
        if not ok:
            nbad += 1
        print(f"{flag} {name:<18} {status:<12} {detail[:60]}")
    print(f"\n{len(C)-nbad}/{len(C)} CTF scripts clean")
