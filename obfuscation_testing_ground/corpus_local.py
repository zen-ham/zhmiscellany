"""Hand-written tricky-construct corpus. Run: python corpus_local.py"""
import textwrap
from harness import run_corpus

P = {}
def add(name, code): P[name] = textwrap.dedent(code)

add("async_await", '''
    import asyncio
    async def f(x):
        await asyncio.sleep(0)
        return x * 2
    async def main():
        r = await asyncio.gather(f(1), f(2), f(3))
        print(sum(r))
    asyncio.run(main())
''')

add("generators", '''
    def gen(n):
        for i in range(n):
            yield i * i
    def passthru(it):
        yield from it
    print(sum(passthru(gen(5))))
''')

add("match_case", '''
    def describe(p):
        match p:
            case (0, 0):
                return "origin"
            case (x, 0):
                return f"x={x}"
            case (0, y):
                return f"y={y}"
            case (x, y) if x == y:
                return "diag"
            case _:
                return "other"
    print(describe((3, 3)), describe((5, 0)), describe((1, 2)))
''')

add("walrus", '''
    data = [1, 2, 3, 4, 5]
    out = []
    while (n := len(data)) > 0:
        out.append(data.pop())
    print(out, n)
''')

add("global_nonlocal", '''
    counter = 0
    def bump():
        global counter
        counter += 1
    def outer():
        x = 10
        def inner():
            nonlocal x
            x += 5
        inner()
        return x
    bump(); bump()
    print(counter, outer())
''')

add("star_unpacking", '''
    a, *mid, b = [1, 2, 3, 4, 5]
    first, second = 10, 20
    def f(*args, **kwargs):
        return sum(args) + sum(kwargs.values())
    print(a, mid, b, f(1, 2, 3, x=4, y=5))
''')

add("comprehensions", '''
    sq = {i: i*i for i in range(5)}
    evens = {x for x in range(10) if x % 2 == 0}
    nested = [[r*c for c in range(3)] for r in range(3)]
    print(sq[4], sorted(evens)[:3], nested[2])
''')

add("fstring_nasty", '''
    name = "world"
    val = 3.14159
    items = {"k": [1, 2]}
    print(f"{name!r} {val:.2f} {items['k'][0]} {1+1=}")
''')

add("inline_compound", '''
    x = 5
    if x > 0: y = 1
    else: y = -1
    for i in range(3): pass
    while False: pass
    print(y)
''')

add("semicolons", '''
    a = 1; b = 2; c = a + b
    d = 0
    print(a, b, c, d)
''')

add("decorators_stacked", '''
    def tag(label):
        def deco(fn):
            def wrap(*a, **k):
                return f"{label}:{fn(*a, **k)}"
            return wrap
        return deco
    @tag("A")
    @tag("B")
    def greet():
        return "hi"
    print(greet())
''')

add("oop_full", '''
    class Animal:
        kind = "?"
        def __init__(self, name):
            self.name = name
        def speak(self):
            return f"{self.name} the {self.kind}"
    class Dog(Animal):
        kind = "dog"
        @property
        def loud(self):
            return self.speak().upper()
        @staticmethod
        def legs():
            return 4
    d = Dog("Rex")
    print(d.speak(), d.loud, Dog.legs())
''')

add("dataclass", '''
    from dataclasses import dataclass, field
    @dataclass
    class Point:
        x: int = 0
        y: int = 0
        tags: list = field(default_factory=list)
        def dist2(self):
            return self.x**2 + self.y**2
    p = Point(3, 4)
    print(p.dist2(), p.tags)
''')

add("exceptions", '''
    def risky(v):
        try:
            if v == 0:
                raise ValueError("zero")
            return 10 / v
        except ValueError as e:
            return str(e)
        except ZeroDivisionError:
            return "div0"
        finally:
            pass
    print(risky(2), risky(0))
''')

add("raise_from", '''
    try:
        try:
            1 / 0
        except ZeroDivisionError as e:
            raise RuntimeError("wrapped") from e
    except RuntimeError as r:
        print(type(r.__cause__).__name__, r)
''')

add("nested_no_trailing_comma", '''
    matrix = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ]
    config = {
        "a": [1, 2],
        "b": {
            "c": 3
        }
    }
    print(matrix[1][2], config["b"]["c"])
''')

add("backslash_chain", '''
    total = 1 + \\
            2 + \\
            3
    cond = total > 0 and \\
           total < 100
    print(total, cond)
''')

add("triple_with_code", '''
    template = """
    def fake():
        x = [1,
        2]
        return x
    """
    print(len(template.splitlines()))
''')

add("docstrings", '''
    """module doc"""
    def f():
        """func doc with var = [1,2,3] inside"""
        return 1
    class C:
        """class doc"""
        def m(self):
            """method doc"""
            return 2
    print(f.__doc__[:4], C.__doc__, f() + C().m())
''')

add("future_import", '''
    from __future__ import annotations
    def f(x: list[int]) -> int:
        return sum(x)
    print(f([1, 2, 3]))
''')

add("type_hints_complex", '''
    from typing import Optional, Dict, List
    def f(a: int, b: Optional[str] = None, *c: float, **d: int) -> Dict[str, List[int]]:
        return {"r": [a]}
    x: Dict[str, int] = {"k": 1}
    print(f(5)["r"], x["k"])
''')

add("unicode_identifiers", '''
    café = 10
    naïve = 20
    Δ = café + naïve
    print(Δ)
''')

add("conditional_expr", '''
    xs = [1, -2, 3, -4]
    ys = [v if v > 0 else -v for v in xs]
    z = "pos" if sum(xs) >= 0 else "neg"
    print(ys, z)
''')

add("with_multiple", '''
    import io
    with io.StringIO() as a, io.StringIO() as b:
        a.write("foo"); b.write("bar")
        r = a.getvalue() + b.getvalue()
    print(r)
''')

add("ellipsis_pass_bodies", '''
    def stub(): ...
    class Empty: pass
    class Proto:
        def m(self): ...
    stub()
    print(Empty.__name__, Proto().m())
''')

add("assert_del", '''
    d = {"a": 1, "b": 2}
    assert "a" in d
    del d["a"]
    x = 5
    del x
    print(list(d))
''')

add("chained_compare", '''
    a, b, c = 1, 2, 3
    r = a < b < c <= 3
    s = 0 <= a < 10
    print(r, s)
''')

add("realistic_primes", '''
    def primes(n):
        sieve = [True] * (n + 1)
        sieve[0] = sieve[1] = False
        for i in range(2, int(n**0.5) + 1):
            if sieve[i]:
                for j in range(i*i, n + 1, i):
                    sieve[j] = False
        return [i for i, p in enumerate(sieve) if p]
    print(primes(30))
''')

add("realistic_wordcount", '''
    text = "the quick brown fox the lazy dog the end"
    counts = {}
    for w in text.split():
        counts[w] = counts.get(w, 0) + 1
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    print(top[:2])
''')

add("class_in_func", '''
    def make(start):
        class Counter:
            value = start
            def inc(self):
                Counter.value += 1
                return Counter.value
        return Counter()
    c = make(10)
    print(c.inc(), c.inc())
''')


if __name__ == "__main__":
    cases = [{"name": n, "code": c} for n, c in P.items()]
    n_ok, n_skip, failures = run_corpus(cases)
    for f in failures:
        print(f"FAIL [{f['status']}] {f['name']}: {f['detail']}")
    print(f"\n{n_ok} ok | {n_skip} skipped | {len(failures)} failed  (of {len(cases)})")
