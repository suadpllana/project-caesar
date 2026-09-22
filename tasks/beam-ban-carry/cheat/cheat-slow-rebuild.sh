#!/bin/bash
# Exactly correct, and rebuilds a beam's spans from its tokens each step.
set -euo pipefail

cat > /app/bm/sc.py <<'PYEOF'
from collections import defaultdict


class Table:
    def __init__(self, rows):
        self.go = defaultdict(list)
        self.end = {}
        for a, b, score in rows:
            if b:
                self.go[a].append((b, score))
            else:
                self.end[a] = score
        for a in self.go:
            self.go[a] = tuple(sorted(self.go[a]))
        self.hi = max([score for _a, _b, score in rows] or [0])

    def out(self, ctx):
        return self.go.get(ctx, ())

    def stop(self, ctx):
        return self.end.get(ctx)

    def top(self):
        return self.hi
PYEOF

cat > /app/bm/rep.py <<'PYEOF'
class Path:
    """Whole token tuple, with the spans it holds as a frozenset beside it."""

    def __init__(self, seq, held, cut):
        self.seq = seq
        self.held = held
        self.cut = cut

    @property
    def last(self):
        return self.seq[-1]

    @property
    def length(self):
        return len(self.seq) - self.cut

    def tokens(self):
        return list(self.seq[self.cut:])

    def span(self, n, tok):
        if len(self.seq) + 1 < n:
            return None
        return self.seq[len(self.seq) + 1 - n:] + (tok,)

    def grow(self, n, tok):
        return Path(self.seq + (tok,), None, self.cut)

    def rebuilt(self, n):
        seq = self.seq
        out = set()
        for i in range(len(seq) - n + 1):
            out.add(seq[i:i + n])
        return out


def root(prompt, n):
    seq = tuple(prompt)
    return Path(seq, None, len(seq))


class Lent:
    """One count per span, kept up to date as members come and go."""

    def __init__(self):
        self.tally = {}

    def take(self, path, n):
        for span in path.rebuilt(n):
            self.tally[span] = self.tally.get(span, 0) + 1

    def give(self, path, n):
        for span in path.rebuilt(n):
            left = self.tally[span] - 1
            if left:
                self.tally[span] = left
            else:
                del self.tally[span]

    def has(self, span):
        return span in self.tally
PYEOF

cat > /app/bm/keep.py <<'PYEOF'
def _key(one):
    return (-one[0], one[1], one[2])


class Pool:
    """Members as plain tuples (fin, ln, order, path); worst is the largest key."""

    def __init__(self, cap):
        self.cap = cap
        self.mem = []
        self.made = 0

    def put(self, fin, ln, path):
        self.made += 1
        self.mem.append((fin, ln, self.made, path))
        dropped = []
        while len(self.mem) > self.cap:
            pos = max(range(len(self.mem)), key=lambda i: _key(self.mem[i]))
            dropped.append(self.mem.pop(pos))
        return dropped

    def full(self):
        return len(self.mem) >= self.cap

    def worst(self):
        return min((one[0] for one in self.mem), default=None)

    def listing(self):
        return sorted(self.mem, key=_key)
PYEOF

cat > /app/bm/pick.py <<'PYEOF'
def take(cands, w):
    out = []
    seen = set()
    for one in sorted(cands, key=lambda c: (-c[0], c[1], c[2])):
        if one[2] not in seen:
            seen.add(one[2])
            out.append(one)
            if len(out) >= w:
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
    tab = sc.Table(sp.rows)
    lent = rep.Lent()
    pool = keep.Pool(sp.h)
    out = [say.ask(name)]
    live = [(0, rep.root(prompt, sp.n))]
    step = 0
    while True:
        step += 1
        for raw, path in live:
            if path.length >= sp.s:
                add = tab.stop(path.last)
                if add is not None:
                    ln = path.length
                    fin = raw + add - sp.p * ln
                    out.append(say.shut(step, ln, fin))
                    lent.take(path, sp.n)
                    for old in pool.put(fin, ln, path):
                        out.append(say.gone(step, old[1], old[0]))
                        lent.give(old[3], sp.n)
        cands = []
        for slot, (raw, path) in enumerate(live):
            held = path.rebuilt(sp.n)
            for tok, add in tab.out(path.last):
                span = path.span(sp.n, tok)
                if span is not None and (span in held or lent.has(span)):
                    continue
                cands.append((raw + add, slot, tok, path))
        took = pick.take(cands, sp.w)
        best = max([c[0] for c in took] or [0])
        stop = halt.why(step, sp.t, took, pool, best, sp.p, tab.top())
        if stop is not None:
            out.append(say.halt(step, stop))
            break
        live = [(c[0], c[3].grow(sp.n, c[2])) for c in took]
    for rank, one_hyp in enumerate(pool.listing()):
        out.append(say.hyp(rank, one_hyp[0], one_hyp[1], one_hyp[3].tokens()))
    return out
PYEOF

cat > /app/bm/halt.py <<'PYEOF'
def why(step, cap, took, pool, best, p, g):
    if not took:
        return "dry"
    if step >= cap:
        return "cap"
    if not pool.full():
        return None
    gain = g - p
    if gain < 0:
        gain = 0
    return "bound" if best - p * step + gain * (cap - step) <= pool.worst() else None
PYEOF

