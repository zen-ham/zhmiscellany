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
