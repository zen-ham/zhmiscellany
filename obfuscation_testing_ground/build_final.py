"""
Transform obfuscator.py (module-level helpers) into obfuscator_final.py: a single
self-contained obfuscate_python function (helpers nested), for a clean drop-in
into misc.py. Then the caller verifies byte-identical output.
"""
import io

with open("obfuscator.py", encoding="utf-8") as fh:
    lines = fh.read().split("\n")

# module docstring = first triple-quoted block
assert lines[0].startswith('"""')
end_doc = next(i for i in range(1, len(lines)) if lines[i].strip().endswith('"""'))
docstring = lines[0:end_doc + 1]

idx_def = next(i for i, l in enumerate(lines) if l.startswith("def obfuscate_python("))
# signature ends at the first line (from def) ending in "):"
idx_sig_end = next(i for i in range(idx_def, len(lines)) if lines[i].rstrip().endswith("):"))

to_nest = lines[end_doc + 1:idx_def]          # imports, constants, helper defs
signature = lines[idx_def:idx_sig_end + 1]      # def ...():
body = lines[idx_sig_end + 1:]                  # original function body (already indented)


def ind(l):
    return ("    " + l) if l.strip() else l


# reuse the module description as the function's docstring (indented one level)
inner = lines[1:end_doc]  # text between the triple quotes
func_doc = ['    """'] + ['    ' + l if l.strip() else l for l in inner] + ['    """']

out = []
out.extend(docstring)
out.append("")
out.append("")
out.extend(signature)
out.extend(func_doc)
out.extend(ind(l) for l in to_nest)
out.extend(body)

with open("obfuscator_final.py", "w", encoding="utf-8") as fh:
    fh.write("\n".join(out))

print(f"wrote obfuscator_final.py ({len(out)} lines)")
