r"""
playground.py -- drive the obfuscator against tons of scripts and see the results.

ITERATION WORKFLOW
  1. Edit  obfuscator.py   (the readable, module-level version)
  2. Run   python playground.py [options]   to see line counts, timing, errors
  3. When happy, push your change into the real package:
         python build_final.py        # regenerate the self-contained obfuscator_final.py
         python port_to_misc.py        # splice it into ../src/zhmiscellany/misc.py
     (build_final verifies obfuscator_final is byte-identical to obfuscator.py;
      port_to_misc verifies the result parses + matches before writing.)

WHERE THE "TONS OF SCRIPTS" COME FROM (mix and match)
  (default)        the curated corpus: 17 original + 30 tricky programs
  --fuzz N         generate N random composed programs (elif/enum/metaclass/match/...)
  --ctf            ~12 realistic crackme/CTF-style scripts with logic worth hiding
  --stdlib N       N real modules sampled from your Python's standard library
  --dir PATH       every *.py under PATH (drop your own "imaginary scripts" here)
  --file X.py      a single script (use with --show to print the obfuscated source)

SEE THE ACTUAL BEFORE/AFTER
  --dump DIR       write a <name>.in.py + <name>.out.py pair per script into DIR, so you
                   have real files to open and diff. Add --keep-prints so the .out.py
                   reproduces the original's output (otherwise prints are stripped).

EXAMPLES
  python playground.py                          # quick correctness+stats on the corpus
  python playground.py --fuzz 300               # 300 random programs
  python playground.py --stdlib 200             # stress on 200 real stdlib modules
  python playground.py --dir my_scripts --all   # your folder, show every row
  python playground.py --file foo.py --show     # obfuscate one file and print it
  python playground.py --ctf --keep-prints --dump pairs   # real before/after files to read
  python playground.py --fuzz 10 --dump pairs   # dump a .in/.out pair for each fuzz
  python playground.py --ratio 25 --seed 3      # tweak obfuscation knobs
  python playground.py --stdlib 400 --quick     # fastest: obfuscate+time+linecount only
  python playground.py --module final           # test the ported obfuscator_final.py instead

WHAT EACH STATUS MEANS
  OK          obfuscated code is valid and (in behavior mode) runs identically to the original
  PARSE-FAIL  obfuscator produced code that won't parse  <-- a real bug
  OUT-MISMATCH / RC-MISMATCH   behavior changed          <-- a real bug
  RUN-TIMEOUT obfuscated code hung
  OBF-ERROR   the obfuscator itself raised               <-- a real bug
  SKIP        original script doesn't run cleanly on its own (can't compare) -- not a bug

CHECK DEPTH
  behavior  (default for corpus/--fuzz/--file): run original vs obfuscated, compare stdout+exit
  compile   (default for --stdlib/--dir): just parse+compile the obfuscated code (safe + fast,
            no side effects from running unknown modules). Force with --check compile|behavior.
  --quick   skip the correctness check entirely; only obfuscate, time it, count lines.
"""
import argparse, ast, os, glob, random, time, tokenize, re, statistics, sys, traceback

import harness  # _run(), check()

# Known side-effect-on-import/run stdlib modules to skip in behavior/run mode.
_STDLIB_SKIP = {"antigravity", "this", "__hello__", "__phello__", "turtle",
                "lib2to3", "idlelib", "tkinter", "ensurepip", "venv"}


def _read(path):
    try:
        with tokenize.open(path) as fh:   # respects coding cookie
            return fh.read()
    except Exception:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()


def _safe(name):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)


def gather(args):
    """Return list of (name, source)."""
    scripts = []
    used_default = not (args.fuzz or args.ctf or args.stdlib or args.dir or args.file)

    if used_default:
        from characterize import CASES
        from corpus_local import P
        scripts += [(f"corpus:{n}", s) for n, s in CASES.items()]
        scripts += [(f"tricky:{n}", s) for n, s in P.items()]

    if args.fuzz:
        import fuzz_local
        rng = random.Random(args.seed if args.seed is not None else 0)
        for i in range(args.fuzz):
            rng.seed(90000 + i)
            scripts.append((f"fuzz:{i}", fuzz_local.make_module_program(rng, rng.randint(2, 6))))

    if args.ctf:
        from corpus_ctf import C
        scripts += [(f"ctf:{n}", s) for n, s in C.items()]

    if args.stdlib:
        stdlib_dir = os.path.dirname(os.__file__)
        files = sorted(glob.glob(os.path.join(stdlib_dir, "*.py")))
        rng = random.Random(args.seed if args.seed is not None else 0)
        rng.shuffle(files)
        picked = 0
        for f in files:
            mod = os.path.splitext(os.path.basename(f))[0]
            if args.check == "behavior" and mod in _STDLIB_SKIP:
                continue
            scripts.append((f"stdlib:{mod}", _read(f)))
            picked += 1
            if picked >= args.stdlib:
                break

    if args.dir:
        for f in sorted(glob.glob(os.path.join(args.dir, "**", "*.py"), recursive=True)):
            scripts.append((f"dir:{os.path.relpath(f, args.dir)}", _read(f)))

    if args.file:
        scripts.append((f"file:{os.path.basename(args.file)}", _read(args.file)))

    return scripts


def evaluate(name, src, O, args):
    """Obfuscate (timed) + measure size + check correctness. Returns a result dict."""
    res = {"name": name, "orig_lines": len(src.split("\n")), "obf_lines": None,
           "ratio": None, "ddef": 0, "dclass": 0, "ms": None,
           "status": None, "detail": ""}
    # --- obfuscate, timed ---
    try:
        t = time.perf_counter()
        obf = O(src, remove_prints=not args.keep_prints, new_line_ratio=args.ratio,
                seed=args.seed, new_lines_target=args.target, entangle=args.entangle)
        res["ms"] = (time.perf_counter() - t) * 1000.0
    except Exception as e:
        res["status"] = "OBF-ERROR"
        res["detail"] = f"{type(e).__name__}: {traceback.format_exc()}"
        return res, None
    res["obf_lines"] = len(obf.split("\n"))
    res["ratio"] = res["obf_lines"] / max(1, res["orig_lines"])
    res["ddef"] = len(re.findall(r"(?m)^\s*(?:async\s+)?def ", obf)) - \
        len(re.findall(r"(?m)^\s*(?:async\s+)?def ", src))
    res["dclass"] = len(re.findall(r"(?m)^\s*class ", obf)) - len(re.findall(r"(?m)^\s*class ", src))

    # --- correctness ---
    if args.quick:
        res["status"] = "OBF-ONLY"
    elif args.check == "compile":
        try:
            compile(obf, name, "exec")
            res["status"] = "OK"
        except SyntaxError as e:
            res["status"] = "PARSE-FAIL"
            res["detail"] = f"line {e.lineno}: {e.msg}"
    else:  # behavior
        ok, status, detail = harness.check(src, new_line_ratio=args.ratio, seed=args.seed,
                                           new_lines_target=args.target, entangle=args.entangle)
        res["status"], res["detail"] = status, detail
    return res, obf


def main():
    ap = argparse.ArgumentParser(description="Drive the obfuscator against many scripts.",
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="See the module docstring for the full workflow.")
    ap.add_argument("--fuzz", type=int, metavar="N", help="generate N random composed programs")
    ap.add_argument("--ctf", action="store_true",
                    help="use the ~12 realistic crackme/CTF-style scripts (corpus_ctf.py)")
    ap.add_argument("--stdlib", type=int, metavar="N", help="sample N modules from the stdlib")
    ap.add_argument("--dir", metavar="PATH", help="run every *.py under PATH (recursive)")
    ap.add_argument("--file", metavar="X.py", help="run a single script")
    ap.add_argument("--ratio", type=float, default=10, help="new_line_ratio (default 10)")
    ap.add_argument("--target", type=float, default=0, help="new_lines_target (default 0)")
    ap.add_argument("--seed", type=int, default=None, help="obfuscation seed (default: deterministic)")
    ap.add_argument("--keep-prints", action="store_true", help="don't strip print() calls")
    ap.add_argument("--entangle", action="store_true", help="enable Tier-2 flow entanglement")
    ap.add_argument("--check", choices=["behavior", "compile"], default=None,
                    help="correctness depth (default: behavior for corpus/fuzz/file, compile for stdlib/dir)")
    ap.add_argument("--quick", action="store_true", help="skip correctness; only obfuscate+time+count")
    ap.add_argument("--module", choices=["obfuscator", "final"], default="obfuscator",
                    help="which implementation to test (default: obfuscator.py)")
    ap.add_argument("--all", action="store_true", help="print every row, not just failures")
    ap.add_argument("--show", action="store_true", help="print the obfuscated source (first script)")
    ap.add_argument("--dump", metavar="DIR", help="write a <name>.in.py + <name>.out.py pair per "
                    "script into DIR (real before/after files you can open and diff)")
    ap.add_argument("--sort", choices=["name", "time", "ratio", "lines"], default="name")
    args = ap.parse_args()

    if args.check is None:
        args.check = "compile" if (args.stdlib or args.dir) else "behavior"

    mod = __import__("obfuscator_final" if args.module == "final" else "obfuscator")
    O = mod.obfuscate_python

    scripts = gather(args)
    if not scripts:
        print("no scripts gathered."); return
    print(f"obfuscator: {args.module} | scripts: {len(scripts)} | check: "
          f"{'quick(none)' if args.quick else args.check} | ratio={args.ratio} target={args.target} "
          f"seed={args.seed} keep_prints={args.keep_prints}\n")

    if args.dump:
        os.makedirs(args.dump, exist_ok=True)

    results, first_obf, dumped = [], None, 0
    t0 = time.perf_counter()
    for name, src in scripts:
        res, obf = evaluate(name, src, O, args)
        results.append(res)
        if first_obf is None and obf is not None:
            first_obf = (name, obf)
        if args.dump:
            base = os.path.join(args.dump, _safe(name))
            with open(base + ".in.py", "w", encoding="utf-8") as f:
                f.write(src)
            if obf is not None:
                with open(base + ".out.py", "w", encoding="utf-8") as f:
                    f.write(obf)
                dumped += 1
    wall = time.perf_counter() - t0

    if args.dump:
        print(f"dumped {dumped} input/output pairs into {os.path.abspath(args.dump)}\n")

    if args.show and first_obf:
        print(f"===== obfuscated: {first_obf[0]} =====")
        print(first_obf[1])
        print("=" * 60 + "\n")

    # ---- per-row table ----
    keyfn = {"name": lambda r: r["name"],
             "time": lambda r: -(r["ms"] or 0),
             "ratio": lambda r: -(r["ratio"] or 0),
             "lines": lambda r: -(r["obf_lines"] or 0)}[args.sort]
    rows = sorted(results, key=keyfn)
    bad = [r for r in results if r["status"] in
           ("PARSE-FAIL", "OUT-MISMATCH", "RC-MISMATCH", "RUN-TIMEOUT", "OBF-ERROR")]

    def fmt(r):
        ms = f"{r['ms']:6.1f}ms" if r["ms"] is not None else "   --  "
        if r["obf_lines"] is None:
            size = f"{r['orig_lines']:>5} -> ERR"
        else:
            size = f"{r['orig_lines']:>5} ->{r['obf_lines']:>6} ({r['ratio']:4.1f}x)"
        deco = f"+{r['ddef']}d +{r['dclass']}c"
        det = f"  {r['detail']}" if r["detail"] else ""
        return f"  {r['status']:<11} {r['name'][:34]:<34} {size} {deco:>9} {ms}{det}"

    show_rows = rows if (args.all or len(rows) <= 40) else bad
    if show_rows:
        if not args.all and len(rows) > 40:
            print(f"(showing {len(show_rows)} non-OK rows; pass --all for every row)\n")
        for r in show_rows:
            print(fmt(r))
        print()

    # ---- slowest / biggest ----
    timed = [r for r in results if r["ms"] is not None]
    if len(timed) > 5:
        print("slowest:")
        for r in sorted(timed, key=lambda r: -r["ms"])[:6]:
            print(f"  {r['ms']:7.1f}ms  {r['name'][:40]}  ({r['orig_lines']} lines)")
        print("biggest growth:")
        for r in sorted([r for r in timed if r["ratio"]], key=lambda r: -r["ratio"])[:6]:
            print(f"  {r['ratio']:5.1f}x   {r['name'][:40]}  ({r['orig_lines']}->{r['obf_lines']})")
        print()

    # ---- summary ----
    from collections import Counter
    counts = Counter(r["status"] for r in results)
    mss = [r["ms"] for r in timed]
    ratios = [r["ratio"] for r in results if r["ratio"]]
    print("summary")
    print("  status:", " | ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    if mss:
        print(f"  obfuscation time: total {sum(mss):.0f}ms | mean {statistics.mean(mss):.1f}ms | "
              f"median {statistics.median(mss):.1f}ms | max {max(mss):.1f}ms")
    if ratios:
        print(f"  line ratio: mean {statistics.mean(ratios):.1f}x | median {statistics.median(ratios):.1f}x | "
              f"max {max(ratios):.1f}x")
    print(f"  wall clock: {wall:.1f}s for {len(scripts)} scripts")
    if bad:
        print(f"\n  *** {len(bad)} REAL FAILURE(S) -- these are obfuscator bugs ***")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
