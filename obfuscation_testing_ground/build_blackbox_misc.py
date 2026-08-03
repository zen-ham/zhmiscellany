"""Ship BLACK-BOX: replace obfuscate_python in src/zhmiscellany/misc.py with a
lazy wrapper that exec()s a self-hosted (obfuscated-by-itself) implementation.
The clean generator never appears in the public package; only its diluted form,
zlib+base64-packed, does. Behaviour is byte-identical to the clean tool."""
import ast, base64, zlib, shutil, sys
sys.path.insert(0, ".")
import obfuscator as O

RATIO = 50           # "50x dilution"
SEED = 20260722
MISC = "../src/zhmiscellany/misc.py"

# 1) self-contained source, minus the __main__ demo (would NameError under exec)
final = open("obfuscator_final.py", encoding="utf-8").read().split("\n")
mi = next(i for i, l in enumerate(final) if l.startswith("if __name__"))
src = "\n".join(final[:mi]).rstrip() + "\n"

# 2) obfuscate it with ITSELF (deterministic), STATIC-BURIAL mode -> the black-box
#    blob. _light keeps the file an unreadable wall of dead template junk but with
#    cheap guards + no live decoys, so the self-hosted tool runs ~10x (not ~300x).
blob = O.obfuscate_python(src, remove_prints=True, new_line_ratio=RATIO,
                          seed=SEED, _light=True)
print(f"blob: {len(blob.splitlines())} lines, {len(blob)//1024} KB")

# 3) verify self-host: blob's obfuscate_python == clean obfuscate_python
ns = {}
exec(blob, ns)
bb = ns["obfuscate_python"]
TESTS = [
    ("import hashlib\ndef f(s):\n    return hashlib.sha256(s.encode()).hexdigest()\nprint(f('x')[:4])\n",
     dict(entangle=True, new_lines_target=6000, seed=3)),
    ("def add(a,b):\n    return a+b\nprint(add(2,3))\n", dict(seed=7, new_line_ratio=8)),
    ("x=[i*i for i in range(5)]\nprint(sum(x))\n", dict(entangle=True, seed=1, new_lines_target=4000)),
]
ok = all(O.obfuscate_python(s, **kw) == bb(s, **kw) for s, kw in TESTS)
assert ok, "SELF-HOST MISMATCH -- blob != clean"
# and the blob's own output still runs
_c = {}; exec(compile(bb(TESTS[0][0], seed=1, new_lines_target=2000), "<t>", "exec"), _c)
print("self-host byte-identical:", ok, "| blob output runs: OK")

# 4) pack
packed = base64.b64encode(zlib.compress(blob.encode("utf-8"), 9)).decode("ascii")
CH = 16384
chunks = [packed[i:i+CH] for i in range(0, len(packed), CH)]
lit = "(\n" + "\n".join('    "%s"' % c for c in chunks) + "\n)"
print(f"packed: {len(packed)//1024} KB base64, {len(chunks)} chunks")

# 5) build the misc.py replacement block
block = '''def obfuscate_python(python_code_string,
                     do_not_obfuscate_indent_block_comment='# DNO',
                     remove_prints=True,
                     remove_comments=True,
                     add_lines=True,
                     new_line_ratio=10,
                     new_lines_target=0,
                     entangle=False,
                     seed=None):
    """Deterministic Python *diluter*: strips prints/comments and injects
    plausible-but-dead decoy code around your real code so the logic is buried in
    junk, without renaming identifiers or adding any decode step. This is the
    black-box build: the implementation is self-hosted (obfuscated by itself) and
    unpacked on first use; behaviour is identical to the reference generator."""
    return _obfuscate_python_impl()(
        python_code_string, do_not_obfuscate_indent_block_comment, remove_prints,
        remove_comments, add_lines, new_line_ratio, new_lines_target, entangle, seed)


_obf_impl_cache = []


def _obfuscate_python_impl():
    if not _obf_impl_cache:
        import base64 as _b64, zlib as _zlib
        _ns = {}
        exec(_zlib.decompress(_b64.b64decode(_OBF_BLACKBOX)).decode("utf-8"), _ns)
        _obf_impl_cache.append(_ns["obfuscate_python"])
    return _obf_impl_cache[0]


_OBF_BLACKBOX = ''' + lit + '\n'

# 6) splice into misc.py (replace the whole current obfuscate_python def)
ml = open(MISC, encoding="utf-8").read().split("\n")
fs = next(i for i, l in enumerate(ml) if l.startswith("def obfuscate_python("))
fe = next(i for i in range(fs + 1, len(ml))
          if ml[i].strip() and not ml[i][:1].isspace())   # next module-level stmt
last = fe - 1
while not ml[last].strip():
    last -= 1
print(f"replacing misc.py lines {fs+1}..{last+1}")
new_ml = ml[:fs] + block.split("\n") + ml[last + 1:]
new_src = "\n".join(new_ml)

tree = ast.parse(new_src)   # must parse
names = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
assert "obfuscate_python" in names and "_obfuscate_python_impl" in names, "not module-level!"

shutil.copy(MISC, MISC + ".prebb.bak")
open(MISC, "w", encoding="utf-8").write(new_src)
print("wrote misc.py (backup at misc.py.prebb.bak) | module-level: OK")

# 7) verify the shipped wrapper works, byte-identical, in isolation
wns = {}
exec("\n".join(block.split("\n")), wns)   # defines wrapper+impl+blob in a clean ns
shipped = wns["obfuscate_python"]
mism = sum(1 for s, kw in TESTS if shipped(s, **kw) != O.obfuscate_python(s, **kw))
print("shipped wrapper byte-identical to clean:", "YES" if mism == 0 else f"NO ({mism})")
