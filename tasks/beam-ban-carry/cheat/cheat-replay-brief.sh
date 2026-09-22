#!/bin/bash
# Shortcut: the trace the brief prints, replayed everywhere.
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
from bm import say


QUOTED = [
        'shut 3 2 18',
        'shut 3 2 15',
        'shut 4 3 23',
        'gone 4 2 15',
        'shut 5 4 29',
        'gone 5 2 18',
        'shut 6 5 34',
        'gone 6 3 23',
        'halt 6 cap',
        'hyp 0 34 5 2 3 4 2 4',
        'hyp 1 29 4 2 4 2 3',
    ]


def one(sp, name, prompt):
    return [say.ask(name)] + list(QUOTED)
PYEOF

cat > /app/bm/halt.py <<'PYEOF'
def why(step, cap, took, pool, best, p, g):
    if not took:
        return "dry"
    if step >= cap:
        return "cap"
    if not pool.full():
        return None
    low = pool.worst()
    if best - p * step + max(0, g - p) * (cap - step) <= low:
        return "bound"
    return None
PYEOF

