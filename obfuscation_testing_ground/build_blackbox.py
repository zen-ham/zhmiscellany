"""Build the shippable BLACK-BOX obfuscator: obfuscate the clean generator with
itself at a fixed seed (deterministic, stable file), verify byte-identical
behavior, and measure import cost at several sizes to choose the ship target."""
import importlib.util, time, sys

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

clean = load('obfuscator_final.py', 'clean_obf')
own = open('obfuscator_final.py', encoding='utf-8').read()

TESTS = [
    ('import hashlib\ndef f(s):\n    return hashlib.sha256(bytes([ord(c) for c in s])).hexdigest()\nprint(f("hi")[:6])\n', dict(entangle=True, new_lines_target=8000, seed=3)),
    ('def add(a,b):\n    return a+b\nprint(add(2,3))\n', dict(seed=7, new_lines_target=5000)),
]

SEED = 1337
for target in (20000, 60000, 100000):
    t0 = time.time()
    blob = clean.obfuscate_python(own, seed=SEED, new_lines_target=target)
    gen_s = time.time() - t0
    fn = f'_bb_{target}.py'
    open(fn, 'w', encoding='utf-8').write(blob)
    lines = blob.count(chr(10)) + 1
    kb = len(blob)//1024
    # import (parse+exec) cost
    t1 = time.time()
    bb = load(fn, f'bb_{target}')
    imp_s = time.time() - t1
    # equivalence
    ok = all(clean.obfuscate_python(s, **kw) == bb.obfuscate_python(s, **kw) for s,kw in TESTS)
    print(f'target={target:>6}: {lines:>7} lines, {kb:>5}KB | gen={gen_s:.2f}s import={imp_s:.2f}s | byte-identical={ok}')
