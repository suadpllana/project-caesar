from keep import cover


def count(a, p):
    n = 0
    for b in a.roll:
        if b in a.out:
            continue
        if cover.keepers(a, b) == [p]:
            n += 1
    return n
