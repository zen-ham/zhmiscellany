"""
Stress entangle=True for behavior safety. Entanglement reassigns a real local to
itself behind an always-true opaque guard; this must NEVER change behavior, even
around globals, closures, nonlocal, identity, and definite-assignment edges.
Runs the whole curated corpus + targeted scope-stress programs with entangle=True.
"""
import textwrap
from harness import check
from characterize import CASES
from corpus_local import P

S = {}
def add(n, c): S[n] = textwrap.dedent(c)

add("global_read", '''
    CONFIG = 100
    def use():
        local = 5
        more = 7
        return local + more + CONFIG   # CONFIG read-only global: must stay global
    print(use())
''')
add("global_declared", '''
    counter = 0
    def bump():
        global counter
        step = 1
        counter = counter + step
    bump(); bump(); bump()
    print(counter)
''')
add("closure_read", '''
    def outer():
        base = 10
        extra = 5
        def inner():
            return base + extra
        base = base + 1
        return inner()
    print(outer())
''')
add("nonlocal_rw", '''
    def outer():
        n = 0
        bump = 2
        def inc():
            nonlocal n
            n = n + bump
        inc(); inc(); inc()
        return n
    print(outer())
''')
add("param_heavy", '''
    def calc(a, b, c, d):
        x = a + b
        y = c + d
        z = x * y
        return z - a
    print(calc(1, 2, 3, 4))
''')
add("reassigned_then_read", '''
    def f(seed):
        acc = seed
        scale = 2
        for i in range(5):
            acc = acc + i
        result = acc * scale
        return result
    print(f(10))
''')
add("identity_sensitive", '''
    def f():
        a = []
        b = a
        a.append(1)
        return (b is a, len(a))
    print(f())
''')
add("mutable_default_like", '''
    def build():
        items = []
        total = 0
        for k in range(4):
            items.append(k)
            total += k
        return items, total
    print(build())
''')
add("module_level_entangle", '''
    x = 5
    y = 10
    z = x + y
    w = z * 2
    print(x, y, z, w)
''')
add("conditional_binding", '''
    def f(flag):
        base = 1
        if flag:
            extra = 10
        else:
            extra = 20
        return base + extra
    print(f(True), f(False))
''')
add("tuple_unpack_locals", '''
    def f():
        a, b = 3, 4
        c, d = b, a
        return a, b, c, d
    print(f())
''')

cases = ([{"name": f"case:{n}", "code": c} for n, c in CASES.items()]
         + [{"name": f"tricky:{n}", "code": c} for n, c in P.items()]
         + [{"name": f"scope:{n}", "code": c} for n, c in S.items()])

nbad = nskip = 0
for c in cases:
    ok, status, detail = check(c["code"], entangle=True)
    if status == "SKIP":
        nskip += 1
    elif not ok:
        print(f"FAIL [{status}] {c['name']}: {detail[:90]}")
        nbad += 1
print(f"\nentangle=True: {len(cases)-nbad-nskip} ok | {nskip} skip | {nbad} FAIL  (of {len(cases)})")
