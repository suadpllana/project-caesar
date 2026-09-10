class Slab:
    def __init__(self, sid, born):
        self.sid = sid
        self.born = born
        self.runs = []


def hold(tab, buck):
    b = tab.buck.get(buck)
    if b is None:
        b = tab.buck[buck] = []
    return b


def held(s):
    n = 0
    for r in s.runs:
        n += r[1] - r[0] + 1
    return n


def rows(tab, buck):
    n = 0
    for s in hold(tab, buck):
        n += held(s)
    return n


def at(tab, buck, key):
    for s in hold(tab, buck):
        for r in s.runs:
            if r[0] <= key <= r[1]:
                return s.sid
    return None


def over(tab, buck, lo, hi):
    out = []
    for s in hold(tab, buck):
        for r in s.runs:
            if r[0] <= hi and lo <= r[1]:
                out.append(s)
                break
    return out


def inside(tab, buck, lo, hi):
    out = []
    for s in hold(tab, buck):
        if s.runs[0][0] >= lo and s.runs[-1][1] <= hi:
            out.append(s)
    return out


def lose(tab, buck, s):
    hold(tab, buck).remove(s)


def join(tab, buck, s):
    b = hold(tab, buck)
    i = 0
    while i < len(b) and b[i].runs[0][0] < s.runs[0][0]:
        i += 1
    b.insert(i, s)
