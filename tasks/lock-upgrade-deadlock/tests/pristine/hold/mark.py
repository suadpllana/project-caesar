from hold import tab

RANK = ("scan", "grow", "pin", "edit", "seal")

OK = set()
for _a, _b in tab.PAIRS:
    OK.add((_a, _b))
    OK.add((_b, _a))


def fits(a, b):
    return (a, b) in OK


def join2(a, b):
    return a if RANK.index(a) >= RANK.index(b) else b


def join(marks):
    out = None
    for m in marks:
        out = m if out is None else join2(out, m)
    return out
