"""
Characterize the CURRENT obfuscate_python behavior: which inputs survive
(obfuscated code parses + runs + produces identical stdout) and which break.

Run:  python characterize.py
"""
import ast, sys, subprocess, tempfile, os, textwrap

import zhmiscellany.misc as m
OBF = m.obfuscate_python

# (name, source) -- each program prints something deterministic.
CASES = {
    "trailing_comma_list": textwrap.dedent('''\
        var = [1,
            2,
            3,
        ]
        print(sum(var))
    '''),
    "no_trailing_comma_list": textwrap.dedent('''\
        var = [1,
            2,
            3
        ]
        print(sum(var))
    '''),
    "multiline_call": textwrap.dedent('''\
        def add(a, b, c):
            return a + b + c
        x = add(1,
                2,
                3)
        print(x)
    '''),
    "dict_literal": textwrap.dedent('''\
        d = {
            "a": 1,
            "b": 2
        }
        print(d["a"] + d["b"])
    '''),
    "if_else": textwrap.dedent('''\
        x = 5
        if x > 3:
            y = 10
        else:
            y = 20
        print(y)
    '''),
    "try_except": textwrap.dedent('''\
        try:
            z = 1 / 1
        except ZeroDivisionError:
            z = 0
        finally:
            w = 99
        print(z + w)
    '''),
    "string_with_hash": textwrap.dedent('''\
        s = "abc # not a comment"
        print(s)
    '''),
    "triple_string": textwrap.dedent('''\
        s = """line1
        line2 with var = [1,2,3]
        line3"""
        print(len(s))
    '''),
    "backslash_continuation": textwrap.dedent('''\
        total = 1 + \\
                2 + \\
                3
        print(total)
    '''),
    "nested_loops": textwrap.dedent('''\
        acc = 0
        for i in range(3):
            for j in range(3):
                acc += i * j
        print(acc)
    '''),
    "class_def": textwrap.dedent('''\
        class Foo:
            def __init__(self, v):
                self.v = v
            def double(self):
                return self.v * 2
        f = Foo(21)
        print(f.double())
    '''),
    "comprehension_multiline": textwrap.dedent('''\
        data = [
            x * 2
            for x in range(5)
            if x % 2 == 0
        ]
        print(sum(data))
    '''),
    "fstring": textwrap.dedent('''\
        name = "world"
        print(f"hello {name} {1+1}")
    '''),
    "decorator": textwrap.dedent('''\
        def deco(fn):
            def inner():
                return fn() + 1
            return inner
        @deco
        def base():
            return 41
        print(base())
    '''),
    "annotations": textwrap.dedent('''\
        x: int = 5
        y: int = 7
        print(x + y)
    '''),
    "lambda_and_slice": textwrap.dedent('''\
        f = lambda a: a[1:3]
        print(f([10, 20, 30, 40]))
    '''),
    "with_stmt": textwrap.dedent('''\
        import io
        with io.StringIO() as buf:
            buf.write("hi")
            out = buf.getvalue()
        print(out)
    '''),
}


def run(src):
    """Run a program, return (ok, stdout_or_error)."""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as fh:
        fh.write(src)
        path = fh.name
    try:
        p = subprocess.run([sys.executable, path], capture_output=True, text=True, timeout=30)
        if p.returncode != 0:
            return False, p.stderr.strip().splitlines()[-1] if p.stderr.strip() else "nonzero exit"
        return True, p.stdout
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    finally:
        os.unlink(path)


def main():
    width = max(len(n) for n in CASES)
    n_pass = n_parsefail = n_runfail = n_mismatch = 0
    for name, src in CASES.items():
        orig_ok, orig_out = run(src)
        try:
            obf = OBF(src, remove_prints=False)
        except Exception as e:
            print(f"{name:<{width}}  OBF-RAISED  {type(e).__name__}: {e}")
            n_runfail += 1
            continue
        # does it parse?
        try:
            ast.parse(obf)
            parses = True
        except SyntaxError as e:
            parses = False
            perr = f"line {e.lineno}: {e.msg}"
        if not parses:
            print(f"{name:<{width}}  PARSE-FAIL  {perr}")
            n_parsefail += 1
            continue
        obf_ok, obf_out = run(obf)
        if not obf_ok:
            print(f"{name:<{width}}  RUN-FAIL    {obf_out}")
            n_runfail += 1
            continue
        if orig_ok and obf_out != orig_out:
            print(f"{name:<{width}}  MISMATCH    orig={orig_out!r} obf={obf_out!r}")
            n_mismatch += 1
            continue
        print(f"{name:<{width}}  OK          out={obf_out!r}")
        n_pass += 1
    total = len(CASES)
    print(f"\n{n_pass}/{total} OK | {n_parsefail} parse-fail | "
          f"{n_runfail} run-fail | {n_mismatch} mismatch")


if __name__ == "__main__":
    main()
