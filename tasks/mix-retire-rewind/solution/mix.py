from feed import deck


def line(box):
    got = box.note.get("line")
    if got is None:
        got = {"segs": [(0, tuple(box.pat), tuple([0] * len(box.lens)))], "shut": False}
        box.note["line"] = got
    return got


def count(pat, j, wide):
    per = pat.count(j)
    if not per:
        return 0
    whole, rest = divmod(wide, len(pat))
    return whole * per + sum(1 for i in range(rest) if pat[i] == j)


def grow(box, slot):
    got = line(box)
    segs = got["segs"]
    while not got["shut"] and segs[-1][0] <= slot:
        start, pat, took = segs[-1]
        span = len(pat)
        first = None
        for j in sorted(set(pat)):
            if not box.hold[j]:
                continue
            left = deck.quota(box, j) - took[j]
            spots = [i for i, s in enumerate(pat) if s == j]
            whole, rest = divmod(left - 1, len(spots))
            at = whole * span + spots[rest]
            if first is None or at < first[0]:
                first = (at, j)
        if first is None:
            got["shut"] = True
            break
        at, j = first
        after = tuple(took[i] + count(pat, i, at + 1) for i in range(len(box.lens)))
        segs.append((start + at + 1, tuple(s for s in pat if s != j), after))


def hold(box, slot):
    grow(box, slot)
    segs = line(box)["segs"]
    lo, hi = 0, len(segs) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if segs[mid][0] <= slot:
            lo = mid
        else:
            hi = mid - 1
    return segs[lo]


def took(box, slot):
    start, pat, took = hold(box, slot)
    return [took[j] + count(pat, j, slot - start) for j in range(len(box.lens))]


def turn(box, slot):
    start, pat, _took = hold(box, slot)
    return pat[(slot - start) % len(pat)]
