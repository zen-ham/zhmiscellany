def xor_bytes(data, key):
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

SECRET = b"flag{x0r_15_n0t_encrypt10n}"
KEY = b"obfuscate"
cipher = xor_bytes(SECRET, KEY)
recovered = xor_bytes(cipher, KEY)
print(cipher.hex())
print(recovered.decode())
