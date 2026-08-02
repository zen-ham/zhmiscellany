"""
Fast local fuzzer focused on the rewritten scope-aware insertion logic.

Each "block" generator emits a self-contained fragment that assigns a known int
to nm<i>. We compose random sets of blocks at module scope, and also wrap them
inside functions / methods / nested scopes, then let the harness confirm the
obfuscated program behaves identically to the original. Stresses: elif, enums,
metaclasses, vars()/__dict__/locals()/globals()/dir() introspection, match
captures + except-as with vocab names, class-level control flow, deep nesting.
"""
import random, textwrap
from harness import run_corpus

VOCAB = ['data', 'value', 'result', 'total', 'index', 'node', 'state', 'config',
         'cache', 'target', 'count', 'item', 'content', 'record', 'status']


def b_elif(i):
    return (f"def f{i}(x):\n"
            f"    if x == 1:\n        return 10\n"
            f"    elif x == 2:\n        return 20\n"
            f"    elif x == 3:\n        return 30\n"
            f"    else:\n        return 0\n"
            f"nm{i} = f{i}(2) + f{i}(3)\n")  # 50


def b_elif_oneline(i):
    return (f"def g{i}(x):\n"
            f"    if x > 0: return 1\n"
            f"    elif x < 0: return 2\n"
            f"    else: return 3\n"
            f"nm{i} = g{i}(-5) * 10\n")  # 20


def b_enum(i):
    return (f"import enum\n"
            f"class Col{i}(enum.Enum):\n    A = 1\n    B = 2\n    C = 3\n"
            f"nm{i} = len(Col{i}) * 100 + sum(c.value for c in Col{i})\n")  # 306


def b_flag(i):
    return (f"import enum\n"
            f"class Perm{i}(enum.Flag):\n    R = enum.auto()\n    W = enum.auto()\n    X = enum.auto()\n"
            f"nm{i} = (Perm{i}.R | Perm{i}.X).value + len(Perm{i})\n")  # 5+3=8


def b_meta(i):
    return (f"class Meta{i}(type):\n"
            f"    def __new__(mcs, n, b, ns):\n"
            f"        c = super().__new__(mcs, n, b, ns)\n"
            f"        c.k = sum(1 for x in ns if not x.startswith('__'))\n"
            f"        return c\n"
            f"class C{i}(metaclass=Meta{i}):\n    a = 1\n    b = 2\n    d = 3\n"
            f"nm{i} = C{i}.k * 100\n")  # 300


def b_vars(i):
    return (f"class D{i}:\n    a = 1\n    b = 2\n    c = 3\n"
            f"nm{i} = len([x for x in vars(D{i}) if not x.startswith('__')]) * 7\n")  # 21


def b_locals_fn(i):
    return (f"def h{i}():\n    p = 1\n    q = 2\n    r = 3\n    return len(locals())\n"
            f"nm{i} = h{i}() * 5\n")  # 15


def b_match_capture(i):
    a, b, c = random.sample(VOCAB, 3)
    return (f"cmd{i} = [5, 6, 7]\n"
            f"match cmd{i}:\n"
            f"    case [{a}, {b}, {c}]:\n"
            f"        nm{i} = locals()['{a}'] + locals()['{b}'] + locals()['{c}']\n")  # 18


def b_except_as(i):
    nm = random.choice(VOCAB)
    return (f"try:\n    raise ValueError(42)\n"
            f"except ValueError as {nm}:\n"
            f"    nm{i} = int(str(locals()['{nm}'].args[0]))\n")  # 42


def b_nested_scopes(i):
    return (f"def outer{i}():\n"
            f"    class Inner{i}:\n"
            f"        def method(self):\n"
            f"            acc = 0\n"
            f"            for k in range(4):\n                acc += k\n"
            f"            return acc\n"
            f"    return Inner{i}().method()\n"
            f"nm{i} = outer{i}() + 100\n")  # 106


def b_class_control_flow(i):
    return (f"class CF{i}:\n"
            f"    total = 0\n"
            f"    for _k in range(5):\n        total += _k\n"
            f"    label = 'x'\n"
            f"nm{i} = CF{i}.total + len([x for x in vars(CF{i}) if not x.startswith('__')])\n")  # 10+3=13


def b_globals_introspect(i):
    return (f"zz{i} = 1\n"
            f"nm{i} = sum(1 for x in globals() if x.startswith('zz{i}')) * 9\n")  # 9


def b_dataclass(i):
    return (f"from dataclasses import dataclass, asdict\n"
            f"@dataclass\nclass P{i}:\n    x: int = 3\n    y: int = 4\n"
            f"nm{i} = len(asdict(P{i}())) * 11 + P{i}().x\n")  # 22+3=25


def b_namedtuple(i):
    return (f"from collections import namedtuple\n"
            f"T{i} = namedtuple('T{i}', ['a', 'b', 'c'])\n"
            f"nm{i} = len(T{i}._fields) * 12\n")  # 36


BLOCKS = [b_elif, b_elif_oneline, b_enum, b_flag, b_meta, b_vars, b_locals_fn,
          b_match_capture, b_except_as, b_nested_scopes, b_class_control_flow,
          b_globals_introspect, b_dataclass, b_namedtuple]


def make_module_program(rng, k):
    chosen = [(rng.choice(BLOCKS), idx) for idx in range(k)]
    parts, names = [], []
    for fn, idx in chosen:
        parts.append(fn(idx))
        names.append(f"nm{idx}")
    code = "\n".join(parts) + "\nprint(" + " + ".join(names) + ")\n"
    return code


def wrap_in_function(block_code, varname, i):
    """Put a single block's logic inside a function body and call it."""
    indented = textwrap.indent(block_code, "    ")
    return (f"def wrapper{i}():\n{indented}    return {varname}\n"
            f"print(wrapper{i}())\n")


def main():
    rng = random.Random(12345)
    cases = []

    # single-block isolation (one of each, several seeds for match/except randomness)
    for fn in BLOCKS:
        for s in range(3):
            rng.seed(1000 + s)  # vary vocab sampling for match/except blocks
            cases.append({"name": f"single_{fn.__name__}_{s}", "code": fn(0) + f"print(nm0)\n"})

    # function-wrapped single blocks (tests injection into the wrapper's scope)
    wrappable = [b_elif, b_elif_oneline, b_locals_fn, b_nested_scopes]
    for j, fn in enumerate(wrappable):
        cases.append({"name": f"wrapped_{fn.__name__}",
                      "code": wrap_in_function(fn(0), "nm0", j)})

    # random multi-block module programs
    for n in range(220):
        rng.seed(7000 + n)
        k = rng.randint(2, 6)
        cases.append({"name": f"mix_{n}", "code": make_module_program(rng, k)})

    n_ok, n_skip, failures = run_corpus(cases)
    for f in failures:
        print(f"FAIL [{f['status']}] {f['name']}: {f['detail']}")
        print(textwrap.indent(f["code"], "    | "))
    print(f"\n{n_ok} ok | {n_skip} skipped | {len(failures)} failed  (of {len(cases)})")


if __name__ == "__main__":
    main()
