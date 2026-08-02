"""
Reusable correctness harness for the obfuscator.

check(src) obfuscates `src` two ways and confirms behavior is preserved:
  * remove_prints=False : obfuscated stdout + return code must match the original
  * remove_prints=True  : obfuscated code must still run (no crash, same rc)
Both forms must also pass ast.parse.

Returns (ok: bool, status: str, detail: str).

CLI:  python harness.py corpus.json     # corpus.json = [{"name","code"}, ...]
"""
import ast, sys, subprocess, tempfile, os, json

from obfuscator import obfuscate_python as OBF


def _run(src, timeout=30):
    fd, path = tempfile.mkstemp(suffix=".py")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(src)
    try:
        p = subprocess.run([sys.executable, path], capture_output=True,
                           text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return None, "", "TIMEOUT"
    finally:
        os.unlink(path)


def check(src, **obf_kwargs):
    # obf_kwargs (e.g. new_line_ratio=, seed=) are forwarded to obfuscate_python;
    # remove_prints is set per-form below and ignored if also passed.
    obf_kwargs.pop("remove_prints", None)
    # baseline
    rc0, out0, err0 = _run(src)
    if rc0 is None:
        return True, "SKIP", "original timed out"
    if rc0 != 0:
        return True, "SKIP", f"original is not a clean program (rc={rc0}): {err0.strip()[-200:]}"

    # form 1: keep prints, must match exactly
    try:
        obf1 = OBF(src, remove_prints=False, **obf_kwargs)
    except Exception as e:
        return False, "OBF-RAISED", f"{type(e).__name__}: {e}"
    try:
        ast.parse(obf1)
    except SyntaxError as e:
        return False, "PARSE-FAIL", f"(keep-prints) line {e.lineno}: {e.msg}"
    rc1, out1, err1 = _run(obf1)
    if rc1 is None:
        return False, "RUN-TIMEOUT", "obfuscated (keep-prints) timed out"
    if rc1 != rc0:
        return False, "RC-MISMATCH", f"rc {rc0} -> {rc1}; err={err1.strip()[-200:]}"
    if out1 != out0:
        return False, "OUT-MISMATCH", f"orig={out0!r} obf={out1!r}"

    # form 2: default (remove prints) must still run cleanly
    try:
        obf2 = OBF(src, remove_prints=True, **obf_kwargs)
        ast.parse(obf2)
    except SyntaxError as e:
        return False, "PARSE-FAIL", f"(remove-prints) line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, "OBF-RAISED", f"(remove-prints) {type(e).__name__}: {e}"
    rc2, out2, err2 = _run(obf2)
    if rc2 is None:
        return False, "RUN-TIMEOUT", "obfuscated (remove-prints) timed out"
    if rc2 != rc0:
        return False, "RC-MISMATCH", f"(remove-prints) rc {rc0} -> {rc2}; err={err2.strip()[-200:]}"

    return True, "OK", f"out={out0!r}"


def run_corpus(cases):
    """cases: list of {name, code}. Returns (n_ok, n_skip, failures[])."""
    n_ok = n_skip = 0
    failures = []
    for c in cases:
        name, code = c["name"], c["code"]
        try:
            ok, status, detail = check(code)
        except Exception as e:
            ok, status, detail = False, "HARNESS-ERROR", repr(e)
        if status == "SKIP":
            n_skip += 1
        elif ok:
            n_ok += 1
        else:
            failures.append({"name": name, "status": status, "detail": detail, "code": code})
    return n_ok, n_skip, failures


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as fh:
        cases = json.load(fh)
    n_ok, n_skip, failures = run_corpus(cases)
    for f in failures:
        print(f"FAIL [{f['status']}] {f['name']}: {f['detail']}")
    print(f"\n{n_ok} ok | {n_skip} skipped | {len(failures)} failed  (of {len(cases)})")
    sys.exit(1 if failures else 0)
