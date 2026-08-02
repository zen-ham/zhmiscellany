try:
    raise ValueError(42)
except ValueError as state:
    nm0 = int(str(locals()['state'].args[0]))

import enum
class Perm1(enum.Flag):
    R = enum.auto()
    W = enum.auto()
    X = enum.auto()
nm1 = (Perm1.R | Perm1.X).value + len(Perm1)

from collections import namedtuple
T2 = namedtuple('T2', ['a', 'b', 'c'])
nm2 = len(T2._fields) * 12

def f3(x):
    if x == 1:
        return 10
    elif x == 2:
        return 20
    elif x == 3:
        return 30
    else:
        return 0
nm3 = f3(2) + f3(3)

print(nm0 + nm1 + nm2 + nm3)
