"""Correct variant ok-b, comparison half: what each blank may be, and how two values meet.

A blank is treated as a value only it holds when it has more than 2n + 1 spare allowed values
(n blanks in the program) and no inequality reaches it; the reference uses n + 1. Both are
sound; the stricter one enumerates more, and the verifier must not care.
"""
import bisect

from rs.dom import Span
from rs.lex import Blank
from rs.rule import ANY, Var

MINE = object()


class Lot:
    def __init__(self, st):
        used = set()
        for t in st.tabs.values():
            for r in t.rows:
                for v in r:
                    if not isinstance(v, Blank):
                        used.add((type(v), v))
        for rl in st.rules:
            for at in rl.atoms:
                for a in at.args:
                    if a is not ANY and not isinstance(a, Var):
                        used.add((type(a), a))
            for _v, c in rl.nots:
                used.add((type(c), c))
        ints = sorted(v for k, v in used if k is int)
        sites = {}
        for t in st.tabs.values():
            for r in t.rows:
                for i, v in enumerate(r):
                    if isinstance(v, Blank):
                        sites.setdefault(v, []).append((t, i))
        against = {}
        for rl in st.rules:
            for v, c in rl.nots:
                for at in rl.atoms:
                    for i, a in enumerate(at.args):
                        if isinstance(a, Var) and a.name == v.name:
                            against.setdefault((at.tab, i), []).append(c)
        n = len(sites)
        self.opts = {}
        for b, where in sites.items():
            spans = [t.cols[i] for t, i in where if isinstance(t.cols[i], Span)]
            picks = [t.cols[i] for t, i in where if not isinstance(t.cols[i], Span)]
            if spans and not picks:
                lo = max(s.lo for s in spans)
                hi = min(s.hi for s in spans)
                size = hi - lo + 1
                taken = bisect.bisect_right(ints, hi) - bisect.bisect_left(ints, lo)
                ok = lambda c, lo=lo, hi=hi: type(c) is int and lo <= c <= hi
                every = lambda lo=lo, hi=hi: list(range(lo, hi + 1))
            else:
                common = set(picks[0].syms)
                for p in picks[1:]:
                    common &= set(p.syms)
                size = len(common)
                taken = sum(1 for s in common if (str, s) in used)
                ok = lambda c, s=frozenset(common): type(c) is str and c in s
                every = lambda s=common: sorted(s)
            if size - taken > 2 * n + 1:
                hit = []
                for t, i in where:
                    for c in against.get((t.name, i), ()):
                        if ok(c) and c not in hit:
                            hit.append(c)
                self.opts[b] = hit + [MINE]
            else:
                self.opts[b] = every()
        self.consts = {b: [o for o in v if o is not MINE] for b, v in self.opts.items()}

    def lone(self, b):
        return len(self.opts[b]) == 1 and self.opts[b][0] is MINE

    def takes(self, b, c):
        return any(type(o) is type(c) and o == c for o in self.consts[b])


def meet(lot, x, y):
    """True, False, or a literal: ("=", blank, const) or ("~", blank, blank)."""
    xb, yb = isinstance(x, Blank), isinstance(y, Blank)
    if not xb and not yb:
        return type(x) is type(y) and x == y
    if xb and yb:
        if x is y:
            return True
        if lot.lone(x) or lot.lone(y):
            return False
        if not any(lot.takes(y, c) for c in lot.consts[x]):
            return False
        return ("~",) + tuple(sorted((x, y), key=lambda b: b.name))
    b, c = (x, y) if xb else (y, x)
    if lot.lone(b) or not lot.takes(b, c):
        return False
    return ("=", b, c)
