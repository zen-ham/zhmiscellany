cmd0 = [5, 6, 7]
match cmd0:
    case [total, record, data]:
        nm0 = locals()['total'] + locals()['record'] + locals()['data']

import enum
class Col1(enum.Enum):
    A = 1
    B = 2
    C = 3
nm1 = len(Col1) * 100 + sum(c.value for c in Col1)

def g2(x):
    if x > 0: return 1
    elif x < 0: return 2
    else: return 3
nm2 = g2(-5) * 10

class CF3:
    total = 0
    for _k in range(5):
        total += _k
    label = 'x'
nm3 = CF3.total + len([x for x in vars(CF3) if not x.startswith('__')])

print(nm0 + nm1 + nm2 + nm3)
