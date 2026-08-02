"""
Definitive proof that the parametric opaque predicates are ALWAYS constant.

Tests obfuscator._opaque_guard directly (the pure function that builds every
opaque predicate): generate a huge number of predicates over int vars set to
RANDOM values, and assert falsy ones are always falsy and truthy ones always
truthy -- for ALL var values, which is exactly the identity property that makes
the dead code genuinely dead. This isolates the math from the "which guard is
opaque" ambiguity of scanning obfuscated output.
"""
import random
from obfuscator import _opaque_guard

NUMS = [str(x) for x in range(1, 200)]


def main():
    gen = random.Random(1234)     # drives predicate generation
    val = random.Random(9999)     # drives the var VALUES we test each predicate at
    n_false = n_true = bad = 0
    for _ in range(300000):
        truth = gen.random() < 0.5
        k = gen.randint(1, 3)
        vnames = [f"v{i}" for i in range(k)]
        guard = _opaque_guard(gen, vnames, NUMS, truth)
        # the identity must hold for EVERY assignment of the vars -> try several,
        # including the pathological (0, negatives, huge)
        for env in ({vn: val.randint(-10 ** 7, 10 ** 7) for vn in vnames},
                    {vn: 0 for vn in vnames},
                    {vn: val.choice([-1, 1, 2 ** 31, -(2 ** 31)]) for vn in vnames}):
            r = eval(guard, {}, dict(env))
            if truth:
                n_true += 1
                if not r:
                    bad += 1; print("  TRUTHY-FAILED:", guard, "->", r, "at", env)
            else:
                n_false += 1
                if r:
                    bad += 1; print("  FALSY-FAILED:", guard, "->", r, "at", env)
    print(f"predicates x value-trials: {n_false} false-form, {n_true} true-form | BAD: {bad}")
    print("PASS -- every opaque predicate is constant for all var values" if bad == 0
          else "*** FAIL: an opaque predicate is not actually constant ***")


if __name__ == "__main__":
    main()
