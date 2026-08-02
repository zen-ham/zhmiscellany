from collections import namedtuple
T0 = namedtuple('T0', ['a', 'b', 'c'])
nm0 = len(T0._fields) * 12

class Meta1(type):
    def __new__(mcs, n, b, ns):
        c = super().__new__(mcs, n, b, ns)
        c.k = sum(1 for x in ns if not x.startswith('__'))
        return c
class C1(metaclass=Meta1):
    a = 1
    b = 2
    d = 3
nm1 = C1.k * 100

import enum
class Perm2(enum.Flag):
    R = enum.auto()
    W = enum.auto()
    X = enum.auto()
nm2 = (Perm2.R | Perm2.X).value + len(Perm2)

try:
    raise ValueError(42)
except ValueError as config:
    nm3 = int(str(locals()['config'].args[0]))

from dataclasses import dataclass, asdict
@dataclass
class P4:
    x: int = 3
    y: int = 4
nm4 = len(asdict(P4())) * 11 + P4().x

print(nm0 + nm1 + nm2 + nm3 + nm4)
