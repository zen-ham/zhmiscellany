"""Stress the live rich decoys: construct-heavy programs must stay behavior-safe
across seeds and entangle modes (the live rich decoys actually execute)."""
import obfuscator as O
from harness import check

PROGS = [
    'import hashlib\nb = bytes([1,2,3,200,201])\nprint(hashlib.sha256(b).hexdigest()[:6], b.hex())',
    'x = [3,1,2]\nx.sort(); x.append(9)\ny = x.copy()\nprint(x, y.pop())',
    's = "Hello World"\nprint(s.upper().split(), s.replace("o","0"), "-".join(["a","b"]))',
    'raw = bytes([255,0,128,64])\nprint(raw.decode("latin1").encode().hex())',
    'nums = [i**2 for i in range(6)]\nprint(sum(nums), max(nums), nums[::-1][0])',
    'd = {}\nfor k in "abc":\n    d[k] = ord(k) ^ 5\nprint(sorted(d.items()))',
    'import base64\nv = base64.b64encode(b"secret").decode()\nprint(v, len(v) % 3)',
    'def f(a, b):\n    return (a << 2) | (b >> 1)\nprint([f(i, i+1) for i in range(4)])',
    't = ("a", 1, "b", 2)\nprint(t[::2], t.count("a"), t.index(2))',
    'total = 0\nfor i, ch in enumerate("wxyz"):\n    total += i * ord(ch)\nprint(total)',
]

if __name__ == "__main__":
    bad = total = 0
    for pi, src in enumerate(PROGS):
        for ent in (False, True):
            for seed in (None, 1, 2, 3, 4):
                total += 1
                ok, status, detail = check(src, entangle=ent, seed=seed, new_lines_target=8000)
                if not ok and status != "SKIP":
                    print(f"FAIL prog{pi} ent={ent} seed={seed} [{status}]: {detail[:120]}")
                    bad += 1
    print(f"\n{total-bad}/{total} construct-heavy live-safety runs OK")
