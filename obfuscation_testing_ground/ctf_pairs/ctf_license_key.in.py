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