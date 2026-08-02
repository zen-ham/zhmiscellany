"""Replay every failure the adversarial workflow found, through the harness."""
import json, sys
from harness import check

OUT = r"C:\Users\zh\AppData\Local\Temp\claude\c--pywork-packages\12317434-ed90-471e-8a58-695474a95412\tasks\w5acrkoey.output"

with open(OUT, encoding="utf-8") as fh:
    data = json.load(fh)
failures = data["result"]["failures"]

# de-dup identical codes (several categories reported the same elif snippets)
seen, cases = set(), []
for f in failures:
    if f["code"] in seen:
        continue
    seen.add(f["code"])
    cases.append(f)

nbad = 0
for f in cases:
    ok, status, detail = check(f["code"])
    tag = "ok " if ok else "FAIL"
    if not ok:
        nbad += 1
    print(f"{tag} [{status:<12}] {f['category']}/{f['name']}: {detail[:90]}")
print(f"\n{len(cases)-nbad}/{len(cases)} previously-failing cases now pass "
      f"({len(failures)} raw, de-duped to {len(cases)})")
sys.exit(1 if nbad else 0)
