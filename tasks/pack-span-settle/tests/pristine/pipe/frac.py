def norm(num, den):
    if num == 0:
        return 0, 1
    a, b = num, den
    while b:
        a, b = b, a % b
    if a < 0:
        a = -a
    return num // a, den // a
