import bisect


class Buck:
    def __init__(self):
        self.rs = []
        self.own = {}
        self.tot = 0


def hold(tab, buck):
    b = tab.buck.get(buck)
    if b is None:
        b = tab.buck[buck] = Buck()
    return b


def rows(tab, buck):
    b = tab.buck.get(buck)
    return b.tot if b is not None else 0


def at(tab, buck, key):
    b = tab.buck.get(buck)
    if b is None:
        return None
    i = bisect.bisect_right(b.rs, key, key=lambda r: r[0]) - 1
    if i >= 0 and key <= b.rs[i][1]:
        return b.rs[i][3]
    return None


def window(b, lo, hi):
    i = bisect.bisect_left(b.rs, lo, key=lambda r: r[0])
    if i and b.rs[i - 1][1] >= lo:
        i -= 1
    return i, bisect.bisect_right(b.rs, hi, key=lambda r: r[0])


def fit(b, i, j, fresh, jr):
    """Replace the window with a rebuilt one, joining anything that now touches."""
    if i and fresh and b.rs[i - 1][1] + 1 == fresh[0][0] \
            and b.rs[i - 1][2:] == fresh[0][2:]:
        fresh[0] = [b.rs[i - 1][0], fresh[0][1], fresh[0][2], fresh[0][3]]
        i -= 1
    if j < len(b.rs) and fresh and fresh[-1][1] + 1 == b.rs[j][0] \
            and b.rs[j][2:] == fresh[-1][2:]:
        fresh[-1] = [fresh[-1][0], b.rs[j][1], fresh[-1][2], fresh[-1][3]]
        j += 1
    jr.append(("w", b, i, len(fresh), b.rs[i:j]))
    b.rs[i:j] = fresh


def count(b, sid, step, jr):
    was = b.own.get(sid, 0)
    jr.append(("o", b, sid, was))
    now = was + step
    if now:
        b.own[sid] = now
        return
    b.own.pop(sid, None)


def weigh(b, step, jr):
    jr.append(("t", b, b.tot))
    b.tot += step


def undo(jr):
    while jr:
        rec = jr.pop()
        tag = rec[0]
        if tag == "w":
            _, b, i, n, old = rec
            b.rs[i:i + n] = old
        elif tag == "o":
            _, b, sid, was = rec
            if was:
                b.own[sid] = was
            else:
                b.own.pop(sid, None)
        else:
            _, b, was = rec
            b.tot = was
