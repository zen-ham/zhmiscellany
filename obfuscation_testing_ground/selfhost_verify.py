"""Self-host proof: obfuscate the obfuscator with ITSELF, then verify the
obfuscated copy is a functional black box (byte-identical output to clean)."""
import importlib.util, hashlib, time

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

clean = load('obfuscator_final.py', 'clean')
own_src = open('obfuscator_final.py', encoding='utf-8').read()

# 1. obfuscate the obfuscator's own source, with itself
t0 = time.time()
selfhosted_src = clean.obfuscate_python(own_src, seed=42, new_lines_target=60000)
build_s = time.time() - t0
open('obfuscator_selfhosted.py', 'w', encoding='utf-8').write(selfhosted_src)
n_lines = selfhosted_src.count(chr(10)) + 1

# 2. load the obfuscated obfuscator as a live module (does it even run?)
sh = load('obfuscator_selfhosted.py', 'selfhosted')

# 3. black-box equivalence: same inputs -> same obfuscated output as clean
TESTS = [
    ('import hashlib\ndef f(s):\n    return hashlib.sha256(bytes([ord(c) for c in s])).hexdigest()\nprint(f("hi")[:6])\n', dict(entangle=True, new_lines_target=8000, seed=3)),
    ('def add(a,b):\n    return a+b\nprint(add(2,3))\n', dict(seed=7, new_lines_target=5000)),
    ('x=[i*i for i in range(10)]\nprint(sum(x))\n', dict(entangle=True, seed=11, new_lines_target=4000)),
]
all_ok = True
for i,(src,kw) in enumerate(TESTS):
    a = clean.obfuscate_python(src, **kw)
    b = sh.obfuscate_python(src, **kw)
    same = a == b
    # also confirm the obfuscated output of that still RUNS
    ns = {}; exec(compile(b, '<t>', 'exec'), ns)
    print(f'test{i}: black-box byte-identical={same}  produced-code-runs=OK')
    all_ok &= same

print(f'\nself-host build: {n_lines} lines in {build_s:.1f}s')
print('SELF-HOST VERIFIED: obfuscated obfuscator == clean obfuscator' if all_ok else '*** MISMATCH ***')
