#!/bin/bash
# Wrong reading: the ceiling is read one step early.
set -euo pipefail

cat > /app/bm/sc.py <<'PYEOF'
class Table:
    __slots__ = ("go", "end", "best")

    def __init__(self, rows):
        go, end, best = {}, {}, 0
        for a, b, score in rows:
            if score > best:
                best = score
            if b == 0:
                end[a] = score
            else:
                go.setdefault(a, []).append((b, score))
        for a in go:
            go[a].sort()
        self.go = go
        self.end = end
        self.best = best

    def out(self, ctx):
        return self.go.get(ctx, ())

    def stop(self, ctx):
        return self.end.get(ctx)

    def top(self):
        return self.best
PYEOF

cat > /app/bm/rep.py <<'PYEOF'
class Book:
    """The span numbering for one request. A span gets a bit the first time it is recorded."""

    __slots__ = ("n", "num")

    def __init__(self, n):
        self.n = n
        self.num = {}

    def find(self, span):
        return self.num.get(span, -1)

    def mark(self, span):
        bit = self.num.get(span)
        if bit is None:
            bit = len(self.num)
            self.num[span] = bit
        return bit


class Path:
    """A beam's sequence, kept as a link to its parent, and the spans that sequence holds."""

    __slots__ = ("prev", "tok", "last", "tail", "mask", "length")

    def __init__(self, prev, tok, last, tail, mask, length):
        self.prev = prev
        self.tok = tok
        self.last = last
        self.tail = tail
        self.mask = mask
        self.length = length

    def holds(self, bit):
        return bit >= 0 and (self.mask >> bit) & 1

    def tokens(self):
        out, here = [], self
        while here.prev is not None:
            out.append(here.tok)
            here = here.prev
        out.reverse()
        return out


def root(book, prompt):
    n = book.n
    mask = 0
    for i in range(len(prompt) - n + 1):
        mask |= 1 << book.mark(tuple(prompt[i:i + n]))
    tail = tuple(prompt[1 - n:]) if n > 1 else ()
    return Path(None, None, prompt[-1], tail, mask, 0)


def reach(book, path, tok):
    """The span a continuation would add, as a bit, or -1 while the sequence is too short."""
    if len(path.tail) < book.n - 1:
        return -1
    return book.find(path.tail + (tok,))


def grow(book, path, tok):
    mask = path.mask
    if len(path.tail) >= book.n - 1:
        mask |= 1 << book.mark(path.tail + (tok,))
    tail = (path.tail + (tok,))[1 - book.n:] if book.n > 1 else ()
    return Path(path, tok, tok, tail, mask, path.length + 1)


class Lent:
    """What the kept set lends the search: the spans of its members, combined."""

    __slots__ = ("mask",)

    def __init__(self):
        self.mask = 0

    def reset(self, masks):
        one = 0
        for mask in masks:
            one |= mask
        self.mask = one

    def has(self, bit):
        return bit >= 0 and (self.mask >> bit) & 1
PYEOF

cat > /app/bm/keep.py <<'PYEOF'
class Hyp:
    __slots__ = ("fin", "ln", "order", "path")

    def __init__(self, fin, ln, order, path):
        self.fin = fin
        self.ln = ln
        self.order = order
        self.path = path


def _rank(one):
    """Better first: higher final score, then the shorter one, then the one that entered first."""
    return (-one.fin, one.ln, one.order)


class Pool:
    __slots__ = ("cap", "mem", "made")

    def __init__(self, cap):
        self.cap = cap
        self.mem = []
        self.made = 0

    def put(self, fin, ln, path):
        self.made += 1
        one = Hyp(fin, ln, self.made, path)
        self.mem.append(one)
        out = []
        while len(self.mem) > self.cap:
            worst = max(self.mem, key=_rank)
            self.mem.remove(worst)
            out.append(worst)
        return one, out

    def full(self):
        return len(self.mem) >= self.cap

    def worst(self):
        if not self.mem:
            return None
        return min(one.fin for one in self.mem)

    def masks(self):
        return [one.path.mask for one in self.mem]

    def listing(self):
        return sorted(self.mem, key=_rank)
PYEOF

cat > /app/bm/pick.py <<'PYEOF'
def take(cands, w):
    """Down the ranking, one beam per final token, at most w of them."""
    cands.sort(key=lambda one: (-one[0], one[1], one[2]))
    out, used = [], set()
    for one in cands:
        if one[2] in used:
            continue
        used.add(one[2])
        out.append(one)
        if len(out) == w:
            break
    return out
PYEOF

cat > /app/bm/walk.py <<'PYEOF'
from bm import halt
from bm import keep
from bm import pick
from bm import rep
from bm import sc
from bm import say


def one(sp, name, prompt):
    out = [say.ask(name)]
    tab = sc.Table(sp.rows)
    book = rep.Book(sp.n)
    lent = rep.Lent()
    pool = keep.Pool(sp.h)
    g = tab.top()
    beams = [(0, rep.root(book, prompt))]
    step = 0
    while True:
        step += 1
        # Every beam that may stop does so, in slot order, before anything else of this step.
        moved = False
        for raw, path in beams:
            if path.length < sp.s:
                continue
            add = tab.stop(path.last)
            if add is None:
                continue
            ln = path.length
            fin = raw + add - sp.p * ln
            _new, went = pool.put(fin, ln, path)
            out.append(say.shut(step, ln, fin))
            moved = True
            for old in went:
                out.append(say.gone(step, old.ln, old.fin))
        if moved:
            lent.reset(pool.masks())
        # A continuation is refused by the beam's own sequence or by a span the set lends.
        cands = []
        for slot, (raw, path) in enumerate(beams):
            for tok, add in tab.out(path.last):
                bit = rep.reach(book, path, tok)
                if bit >= 0 and (path.holds(bit) or lent.has(bit)):
                    continue
                cands.append((raw + add, slot, tok, path))
        took = pick.take(cands, sp.w)
        best = max((cand[0] for cand in took), default=0)
        reason = halt.why(step, sp.t, took, pool, best, sp.p, g)
        if reason is not None:
            out.append(say.halt(step, reason))
            break
        beams = [(cand[0], rep.grow(book, cand[3], cand[2])) for cand in took]
    for rank, one_hyp in enumerate(pool.listing()):
        out.append(say.hyp(rank, one_hyp.fin, one_hyp.ln, one_hyp.path.tokens()))
    return out
PYEOF

cat > /app/bm/halt.py <<'PYEOF'
def why(step, cap, took, pool, best, p, g):
    if not took:
        return "dry"
    if step >= cap - 1:
        return "cap"
    if not pool.full():
        return None
    low = pool.worst()
    if best - p * step + max(0, g - p) * (cap - step) <= low:
        return "bound"
    return None
PYEOF

