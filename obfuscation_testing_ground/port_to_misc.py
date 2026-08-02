"""
Replace obfuscate_python in src/zhmiscellany/misc.py with the new self-contained
version, placing it at MODULE LEVEL (out of the `if WIN32_AVAILABLE:` block) so
it's defined cross-platform and ships+works in zhmiscellanylite on servers.
Backs up first; verifies the result parses, that obfuscate_python is at module
scope (not WIN32-gated), and that the ported function matches the verified one.
"""
import ast, shutil, textwrap

MISC = "../src/zhmiscellany/misc.py"
FINAL = "obfuscator_final.py"

# ---- extract new function from the self-contained file (already at col 0) ----
fl = open(FINAL, encoding="utf-8").read().split("\n")
gs = next(i for i, l in enumerate(fl) if l.startswith("def obfuscate_python("))
ge = len(fl)
for i in range(gs + 1, len(fl)):
    if fl[i].strip() and not fl[i].startswith((" ", "\t")):  # next col-0 stmt ends the fn
        ge = i
        break
new_fn = fl[gs:ge]
while new_fn and not new_fn[-1].strip():
    new_fn.pop()
new_fn = [""] + new_fn  # blank line so it cleanly closes the preceding if-block

# ---- locate + remove the old function (robust to its current indent) ----
ml = open(MISC, encoding="utf-8").read().split("\n")
fstart = next(i for i, l in enumerate(ml) if l.lstrip().startswith("def obfuscate_python("))
old_indent = len(ml[fstart]) - len(ml[fstart].lstrip())
fend = next(i for i in range(fstart + 1, len(ml))
            if ml[i].strip() and (len(ml[i]) - len(ml[i].lstrip())) <= old_indent
            and not ml[i].lstrip().startswith(("def ", "async def ")))
last = fend - 1
while not ml[last].strip():
    last -= 1
# also drop a now-trailing blank line that separated old fn from its predecessor
while fstart > 0 and not ml[fstart - 1].strip():
    fstart -= 1
print(f"replacing misc.py lines {fstart+1}..{last+1} (old indent={old_indent})")

new_ml = ml[:fstart] + new_fn + ml[last + 1:]
new_src = "\n".join(new_ml)
tree = ast.parse(new_src)  # must still be valid Python

# verify obfuscate_python is now a MODULE-LEVEL def (not nested under any if/with)
top_defs = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
assert "obfuscate_python" in top_defs, "obfuscate_python is NOT at module level!"
print("misc.py parses + obfuscate_python is module-level (out of WIN32): OK")

shutil.copy(MISC, MISC + ".bak")
with open(MISC, "w", encoding="utf-8") as fh:
    fh.write(new_src)
print("wrote misc.py (backup at misc.py.bak)")

# ---- verify the ported function matches the verified one ----
ml2 = new_src.split("\n")
s = next(i for i, l in enumerate(ml2) if l.startswith("def obfuscate_python("))
e = next(i for i in range(s + 1, len(ml2))
         if ml2[i].strip() and not ml2[i][:1].isspace())
func_src = "\n".join(ml2[s:e])
ns = {}
exec(func_src, ns)
ported = ns["obfuscate_python"]

import sys
sys.path.insert(0, ".")
from characterize import CASES
import corpus_local
import obfuscator_final as B

srcs = list(CASES.values()) + list(corpus_local.P.values())
mism = sum(1 for src in srcs for rp in (True, False) for r in (10, 3)
           if ported(src, remove_prints=rp, new_line_ratio=r)
           != B.obfuscate_python(src, remove_prints=rp, new_line_ratio=r))
print("ported function byte-identical to verified version:",
      "YES" if mism == 0 else f"NO ({mism})")
