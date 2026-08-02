from dataclasses import dataclass, asdict
@dataclass
class P0:
    x: int = 3
    y: int = 4
nm0 = len(asdict(P0())) * 11 + P0().x

try:
    raise ValueError(42)
except ValueError as node:
    nm1 = int(str(locals()['node'].args[0]))

try:
    raise ValueError(42)
except ValueError as result:
    nm2 = int(str(locals()['result'].args[0]))

def outer3():
    class Inner3:
        def method(self):
            acc = 0
            for k in range(4):
                acc += k
            return acc
    return Inner3().method()
nm3 = outer3() + 100

def outer4():
    class Inner4:
        def method(self):
            acc = 0
            for k in range(4):
                acc += k
            return acc
    return Inner4().method()
nm4 = outer4() + 100

print(nm0 + nm1 + nm2 + nm3 + nm4)
