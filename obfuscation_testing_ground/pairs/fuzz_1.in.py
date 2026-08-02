cmd0 = [5, 6, 7]
match cmd0:
    case [item, target, state]:
        nm0 = locals()['item'] + locals()['target'] + locals()['state']

zz1 = 1
nm1 = sum(1 for x in globals() if x.startswith('zz1')) * 9

class CF2:
    total = 0
    for _k in range(5):
        total += _k
    label = 'x'
nm2 = CF2.total + len([x for x in vars(CF2) if not x.startswith('__')])

class CF3:
    total = 0
    for _k in range(5):
        total += _k
    label = 'x'
nm3 = CF3.total + len([x for x in vars(CF3) if not x.startswith('__')])

zz4 = 1
nm4 = sum(1 for x in globals() if x.startswith('zz4')) * 9

print(nm0 + nm1 + nm2 + nm3 + nm4)
