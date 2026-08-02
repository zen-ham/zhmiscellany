# the "flag" is the unique (a, b, c) satisfying these constraints
def solve():
    for a in range(1, 10):
        for b in range(1, 10):
            for c in range(1, 10):
                if a * 3 + b * 7 == 47 and a * b == 20 and a + b + c == 12:
                    return (a, b, c)
    return None

print(solve())
