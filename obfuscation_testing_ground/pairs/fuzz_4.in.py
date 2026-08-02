zz0 = 1
nm0 = sum(1 for x in globals() if x.startswith('zz0')) * 9

cmd1 = [5, 6, 7]
match cmd1:
    case [item, record, content]:
        nm1 = locals()['item'] + locals()['record'] + locals()['content']

def h2():
    p = 1
    q = 2
    r = 3
    return len(locals())
nm2 = h2() * 5

print(nm0 + nm1 + nm2)
