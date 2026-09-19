from feed import deck


def count(pat, j, wide):
    per = pat.count(j)
    if not per:
        return 0
    whole, rest = divmod(wide, len(pat))
    return whole * per + sum(1 for i in range(rest) if pat[i] == j)


def solve(box, slot):
    """Re-solve the retirements from the opening mix, every time, keeping nothing."""
    start = 0
    pat = tuple(box.pat)
    took = [0] * len(box.lens)
    while True:
        first = None
        for j in sorted(set(pat)):
            if not box.hold[j]:
                continue
            need = deck.fits(box, j) * box.hold[j] - took[j]
            spots = [i for i, s in enumerate(pat) if s == j]
            whole, rest = divmod(need - 1, len(spots))
            at = whole * len(pat) + spots[rest]
            if first is None or at < first[0]:
                first = (at, j)
        if first is None or start + first[0] >= slot:
            return start, pat, took
        at, j = first
        took = [took[i] + count(pat, i, at + 1) for i in range(len(box.lens))]
        start = start + at + 1
        pat = tuple(s for s in pat if s != j)


def hold(box, slot):
    return solve(box, slot)


def took(box, slot):
    start, pat, base = solve(box, slot)
    return [base[j] + count(pat, j, slot - start) for j in range(len(box.lens))]


def turn(box, slot):
    start, pat, _base = solve(box, slot)
    return pat[(slot - start) % len(pat)]
