import enum
class Col0(enum.Enum):
    A = 1
    B = 2
    C = 3
nm0 = len(Col0) * 100 + sum(c.value for c in Col0)

class D1:
    a = 1
    b = 2
    c = 3
nm1 = len([x for x in vars(D1) if not x.startswith('__')]) * 7

def g2(x):
    if x > 0: return 1
    elif x < 0: return 2
    else: return 3
nm2 = g2(-5) * 10

def h3():
    p = 1
    q = 2
    r = 3
    return len(locals())
nm3 = h3() * 5

import enum
class Perm4(enum.Flag):
    R = enum.auto()
    W = enum.auto()
    X = enum.auto()
nm4 = (Perm4.R | Perm4.X).value + len(Perm4)

print(nm0 + nm1 + nm2 + nm3 + nm4)
