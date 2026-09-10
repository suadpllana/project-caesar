import bisect


class Buck:
    def __init__(self):
        self.run = {}
        self.key = []
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
    if b is None or not b.key:
        return None
    i = bisect.bisect_right(b.key, key) - 1
    if i < 0:
        return None
    start = b.key[i]
    end, _num, sid = b.run[start]
    return sid if key <= end else None


def meet(b, lo, hi):
    i = bisect.bisect_left(b.key, lo)
    if i and b.run[b.key[i - 1]][0] >= lo:
        i -= 1
    return b.key[i:bisect.bisect_right(b.key, hi)]


def erase(b, start, jr):
    end, num, sid = b.run[start]
    jr.append(("r", b, start, [end, num, sid]))
    del b.run[start]
    del b.key[bisect.bisect_left(b.key, start)]
    count(b, sid, start - end - 1, jr)
    weigh(b, start - end - 1, jr)
    return end, num, sid


def write(b, start, end, num, sid, jr):
    jr.append(("r", b, start, None))
    b.run[start] = [end, num, sid]
    b.key.insert(bisect.bisect_left(b.key, start), start)
    count(b, sid, end - start + 1, jr)
    weigh(b, end - start + 1, jr)


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
        if tag == "r":
            _, b, start, val = rec
            if start in b.run:
                del b.run[start]
                del b.key[bisect.bisect_left(b.key, start)]
            if val is not None:
                b.run[start] = val
                b.key.insert(bisect.bisect_left(b.key, start), start)
        elif tag == "o":
            _, b, sid, was = rec
            if was:
                b.own[sid] = was
            else:
                b.own.pop(sid, None)
        else:
            _, b, was = rec
            b.tot = was
