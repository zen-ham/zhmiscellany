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
