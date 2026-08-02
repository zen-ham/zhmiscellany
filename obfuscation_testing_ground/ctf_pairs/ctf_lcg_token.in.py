def lcg_stream(seed, n):
    x = seed
    out = []
    for _ in range(n):
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        out.append(x % 100)
    return out

token = lcg_stream(0x1337, 6)
print("-".join(f"{v:02d}" for v in token))
