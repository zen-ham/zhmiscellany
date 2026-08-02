"""
Verify the NEW obfuscator: for each case, obfuscated code must parse, run, and
(with prints kept) produce identical stdout to the original. Also report how
much decoy code was injected and whether decoy funcs/classes appear.
"""
import ast, sys, subprocess, tempfile, os, re
from characterize import CASES, run
from obfuscator import obfuscate_python as OBF


def main():
    width = max(len(n) for n in CASES)
    npass = nfail = 0
    for name, src in CASES.items():
        orig_ok, orig_out = run(src)
        try:
            obf = OBF(src, remove_prints=False)
        except Exception as e:
            print(f"{name:<{width}}  OBF-RAISED  {type(e).__name__}: {e}")
            nfail += 1
            continue
        try:
            ast.parse(obf)
        except SyntaxError as e:
            print(f"{name:<{width}}  PARSE-FAIL  line {e.lineno}: {e.msg}")
            nfail += 1
            continue
        obf_ok, obf_out = run(obf)
        if not obf_ok:
            print(f"{name:<{width}}  RUN-FAIL    {obf_out}")
            nfail += 1
            continue
        if orig_ok and obf_out != orig_out:
            print(f"{name:<{width}}  MISMATCH    orig={orig_out!r} obf={obf_out!r}")
            nfail += 1
            continue
        grew = len(obf.split('\n')) - len(src.split('\n'))
        nfuncs = len(re.findall(r'\bdef ', obf)) - len(re.findall(r'\bdef ', src))
        ncls = len(re.findall(r'\bclass ', obf)) - len(re.findall(r'\bclass ', src))
        print(f"{name:<{width}}  OK   +{grew:>4} lines  +{nfuncs} def  +{ncls} class")
        npass += 1
    print(f"\n{npass}/{len(CASES)} OK")


if __name__ == '__main__':
    main()
