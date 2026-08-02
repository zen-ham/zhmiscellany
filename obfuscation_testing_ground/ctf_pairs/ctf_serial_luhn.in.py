def luhn_ok(num):
    digits = [int(d) for d in num if d.isdigit()]
    checksum = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0

for s in ["4539578763621486", "1234567890123456", "79927398713"]:
    print(s, luhn_ok(s))
