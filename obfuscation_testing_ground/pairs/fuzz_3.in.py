from collections import namedtuple
T0 = namedtuple('T0', ['a', 'b', 'c'])
nm0 = len(T0._fields) * 12

class D1:
    a = 1
    b = 2
    c = 3
nm1 = len([x for x in vars(D1) if not x.startswith('__')]) * 7

from collections import namedtuple
T2 = namedtuple('T2', ['a', 'b', 'c'])
nm2 = len(T2._fields) * 12

import enum
class Col3(enum.Enum):
    A = 1
    B = 2
    C = 3
nm3 = len(Col3) * 100 + sum(c.value for c in Col3)

cmd4 = [5, 6, 7]
match cmd4:
    case [node, total, count]:
        nm4 = locals()['node'] + locals()['total'] + locals()['count']

print(nm0 + nm1 + nm2 + nm3 + nm4)
