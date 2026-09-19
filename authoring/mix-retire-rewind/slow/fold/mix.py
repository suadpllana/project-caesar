from feed import deck


def run(box, slot):
    """Step the mix forward one slot at a time to see where each stretch begins."""
    pat = list(box.pat)
    base = 0
    took = [0] * len(box.lens)
    at = 0
    while at < slot:
        j = pat[(at - base) % len(pat)]
        took[j] += 1
        at += 1
        if box.hold[j] and took[j] >= deck.fits(box, j) * box.hold[j]:
            pat = [s for s in pat if s != j]
            base = at
    return base, tuple(pat), took


def count(pat, j, wide):
    per = pat.count(j)
    if not per:
        return 0
    whole, rest = divmod(wide, len(pat))
    return whole * per + sum(1 for i in range(rest) if pat[i] == j)


def hold(box, slot):
    base, pat, took = run(box, slot)
    return base, pat, tuple(t - count(pat, i, slot - base) for i, t in enumerate(took))


def took(box, slot):
    return list(run(box, slot)[2])


def turn(box, slot):
    base, pat, _took = run(box, slot)
    return pat[(slot - base) % len(pat)]
