import bisect

from feed import deck


def board(box):
    got = box.note.get("board")
    if got is None:
        got = {"at": [0], "pat": [list(box.pat)], "took": [[0] * len(box.lens)], "end": False}
        box.note["board"] = got
    return got


def count(pat, j, wide):
    whole, rest = divmod(wide, len(pat))
    return whole * pat.count(j) + pat[:rest].count(j)


def grow(box, slot):
    got = board(box)
    while not got["end"] and got["at"][-1] <= slot:
        pat, took = got["pat"][-1], got["took"][-1]
        picks = []
        for j in sorted(set(pat)):
            if not box.hold[j]:
                continue
            need = deck.fits(box, j) * box.hold[j] - took[j]
            step = len(pat)
            hi = step
            while count(pat, j, hi + 1) < need:
                hi *= 2
            lo = 0
            while lo < hi:
                mid = (lo + hi) // 2
                if count(pat, j, mid + 1) >= need:
                    hi = mid
                else:
                    lo = mid + 1
            picks.append((lo, j))
        if not picks:
            got["end"] = True
            return
        at, j = min(picks)
        got["at"].append(got["at"][-1] + at + 1)
        got["pat"].append([s for s in pat if s != j])
        got["took"].append([took[i] + count(pat, i, at + 1) for i in range(len(box.lens))])


def seat(box, slot):
    grow(box, slot)
    got = board(box)
    return bisect.bisect_right(got["at"], slot) - 1


def hold(box, slot):
    got = board(box)
    i = seat(box, slot)
    return got["at"][i], got["pat"][i], got["took"][i]


def took(box, slot):
    start, pat, base = hold(box, slot)
    return [base[j] + count(pat, j, slot - start) for j in range(len(box.lens))]


def turn(box, slot):
    start, pat, _base = hold(box, slot)
    return pat[(slot - start) % len(pat)]
