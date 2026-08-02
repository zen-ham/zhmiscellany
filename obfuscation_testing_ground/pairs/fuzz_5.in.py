def h0():
    p = 1
    q = 2
    r = 3
    return len(locals())
nm0 = h0() * 5

class D1:
    a = 1
    b = 2
    c = 3
nm1 = len([x for x in vars(D1) if not x.startswith('__')]) * 7

def f2(x):
    if x == 1:
        return 10
    elif x == 2:
        return 20
    elif x == 3:
        return 30
    else:
        return 0
nm2 = f2(2) + f2(3)

class D3:
    a = 1
    b = 2
    c = 3
nm3 = len([x for x in vars(D3) if not x.startswith('__')]) * 7

class D4:
    a = 1
    b = 2
    c = 3
nm4 = len([x for x in vars(D4) if not x.startswith('__')]) * 7

zz5 = 1
nm5 = sum(1 for x in globals() if x.startswith('zz5')) * 9

print(nm0 + nm1 + nm2 + nm3 + nm4 + nm5)
