#!/bin/bash
# five cell claims in a unit before an ask is raised, not four
set -euo pipefail

cat > /app/hold/book.py <<'PYEOF'
"""The claim book: the scope and mode arithmetic, and what every job holds.

A unit covers itself and every cell of it; a cell covers only itself. Two scopes overlap when
either covers the other, and claims held by different jobs conflict when their scopes overlap
and at least one of them is a write. Every overlap is therefore inside one unit, which is why
claims are indexed by unit: the jobs holding the unit itself, the jobs holding each cell of
it, and per job a pair of counts of the cell claims it holds there by mode. The counts are
what make a whole-unit ask answerable without walking the unit's cells.

`bh` is kept alongside: the jobs that hold a claim and also have an ask waiting. Every loop of
jobs held up only by one another contains one of them, so it is the seed set for the stall
search and has to be maintained rather than recomputed.
"""
from hold import name


def covers(a, b):
    if a == b:
        return True
    ua, ca = name.cut(a)
    ub, cb = name.cut(b)
    return ca is None and cb is not None and ua == ub


def overlap(a, b):
    return covers(a, b) or covers(b, a)


def clash(m, n):
    return m == "w" or n == "w"


def atleast(have, want):
    return have == "w" or want == "r"


def strongest(*modes):
    return "w" if "w" in modes else "r"


class Hold:
    def __init__(self):
        self.out = []
        self.held = {}
        self.own = {}
        self.cell = {}
        self.tally = {}
        self.tot = {}
        self.ask = {}
        self.line = {}
        self.byunit = {}
        self.bh = set()
        self.born = {}
        self.nborn = 0
        self.nfile = 0


def wake(h, job):
    if job not in h.born:
        h.nborn += 1
        h.born[job] = h.nborn


def rest(h, job):
    if not h.held.get(job) and job not in h.ask:
        h.held.pop(job, None)
        h.born.pop(job, None)
        h.bh.discard(job)


def recheck(h, job):
    if job in h.ask and h.held.get(job):
        h.bh.add(job)
    else:
        h.bh.discard(job)


def _bump(box, job, mode, by):
    pair = box.setdefault(job, [0, 0])
    pair[0 if mode == "r" else 1] += by
    if not pair[0] and not pair[1]:
        del box[job]


def put(h, job, scope, mode):
    u, c = name.cut(scope)
    mine = h.held.setdefault(job, {})
    old = mine.get(scope)
    if old == mode:
        return
    mine[scope] = mode
    if c is None:
        h.own.setdefault(u, {})[job] = mode
        return
    h.cell.setdefault(u, {}).setdefault(scope, {})[job] = mode
    tal = h.tally.setdefault(u, {})
    tot = h.tot.setdefault(u, [0, 0])
    if old is not None:
        _bump(tal, job, old, -1)
        tot[0 if old == "r" else 1] -= 1
    _bump(tal, job, mode, 1)
    tot[0 if mode == "r" else 1] += 1


def lose(h, job, scope):
    mine = h.held.get(job)
    if not mine or scope not in mine:
        return False
    mode = mine.pop(scope)
    u, c = name.cut(scope)
    if c is None:
        by = h.own.get(u)
        if by is not None:
            by.pop(job, None)
            if not by:
                del h.own[u]
        return True
    by = h.cell.get(u, {}).get(scope)
    if by is not None:
        by.pop(job, None)
        if not by:
            del h.cell[u][scope]
            if not h.cell[u]:
                del h.cell[u]
    _bump(h.tally.get(u, {}), job, mode, -1)
    tot = h.tot.get(u)
    if tot is not None:
        tot[0 if mode == "r" else 1] -= 1
    return True


def holds_over(h, job, scope):
    u, c = name.cut(scope)
    if h.own.get(u, {}).get(job) is not None:
        return True
    if c is None:
        return job in h.tally.get(u, {})
    return job in h.cell.get(u, {}).get(scope, {})


def covered(h, job, scope, mode):
    u, c = name.cut(scope)
    have = h.own.get(u, {}).get(job)
    if have is not None and atleast(have, mode):
        return True
    if c is None:
        return False
    have = h.cell.get(u, {}).get(scope, {}).get(job)
    return have is not None and atleast(have, mode)


def anyclash(h, job, scope, mode):
    """Does a claim of another job conflict with this ask? Answered from one unit."""
    u, c = name.cut(scope)
    for k, m in h.own.get(u, {}).items():
        if k != job and clash(mode, m):
            return True
    if c is None:
        tot = h.tot.get(u)
        if not tot:
            return False
        mine = h.tally.get(u, {}).get(job) or (0, 0)
        if mode == "w":
            return (tot[0] - mine[0] + tot[1] - mine[1]) > 0
        return (tot[1] - mine[1]) > 0
    for k, m in h.cell.get(u, {}).get(scope, {}).items():
        if k != job and clash(mode, m):
            return True
    return False


def whoclash(h, job, scope, mode):
    """The jobs whose claims conflict with this ask. Only the stall search needs them."""
    u, c = name.cut(scope)
    out = set()
    for k, m in h.own.get(u, {}).items():
        if k != job and clash(mode, m):
            out.add(k)
    if c is None:
        for k, pair in h.tally.get(u, {}).items():
            if k == job:
                continue
            if mode == "w" or pair[1]:
                out.add(k)
    else:
        for k, m in h.cell.get(u, {}).get(scope, {}).items():
            if k != job and clash(mode, m):
                out.add(k)
    return out


def clear(h, job):
    """Everything the job holds, plus its ask. Returns what was released and where."""
    units = set()
    mine = h.held.get(job) or {}
    n = len(mine)
    for scope in list(mine):
        units.add(name.cut(scope)[0])
        lose(h, job, scope)
    req = h.ask.get(job)
    if req is not None:
        units.add(name.cut(req[2])[0])
        unfile(h, req)
    h.held.pop(job, None)
    h.born.pop(job, None)
    h.bh.discard(job)
    return n, units, req is not None


def unfile(h, req):
    fid, job = req[0], req[1]
    h.line.pop(fid, None)
    h.ask.pop(job, None)
    box = h.byunit.get(name.cut(req[2])[0])
    if box is not None:
        box.pop(fid, None)


def listing(h, unit):
    rows = []
    for job, mode in h.own.get(unit, {}).items():
        rows.append((h.born[job], (0, 0), job, unit, mode))
    for scope, by in h.cell.get(unit, {}).items():
        for job, mode in by.items():
            rows.append((h.born[job], name.rank(scope), job, scope, mode))
    rows.sort()
    return ",".join("%s@%s=%s" % (r[2], r[3], r[4]) for r in rows)


def onunit(h, unit):
    return len(h.byunit.get(unit, ()))
PYEOF

cat > /app/hold/line.py <<'PYEOF'
"""The waiting line: its order, the refusal test, and the settling pass.

The order is not stored. An ask stands ahead of the line exactly while its job holds a claim
overlapping what the ask asked for, which is read off the book at the moment the order is
needed rather than recorded on the ask: an ordinary drop, a whole-unit claim swallowing the
job's cell claims, and a cancellation all change it under an ask that is already waiting.
Filing order breaks ties inside each group.

Settling walks the asks on the units something was just released from, in that order, and
grants each one that is grantable when it is reached. Restarting from the top of the whole
line after every grant is also correct and is the family the execution limit rules out: a
grant only ever adds or strengthens a claim, and a claim a job gives up when a whole-unit
claim swallows it is covered by that claim, so no grant can make an ask earlier in the order
grantable. One pass is therefore complete.
"""
from hold import book, name, say


def rankof(h, req):
    return (0 if book.holds_over(h, req[1], req[2]) else 1, req[0])


def ahead(h, req):
    """Does an ask of another job standing ahead of this one conflict with it?"""
    mine = rankof(h, req)
    box = h.byunit.get(name.cut(req[2])[0])
    if not box:
        return False
    for fid, other in box.items():
        if fid == req[0] or other[1] == req[1]:
            continue
        if not book.overlap(req[2], other[2]) or not book.clash(req[3], other[3]):
            continue
        if rankof(h, other) < mine:
            return True
    return False


def grantable(h, req):
    if book.anyclash(h, req[1], req[2], req[3]):
        return False
    return not ahead(h, req)


def file_(h, req):
    h.line[req[0]] = req
    h.ask[req[1]] = req
    h.byunit.setdefault(name.cut(req[2])[0], {})[req[0]] = req
    book.recheck(h, req[1])
    say.wait(h, req[1], req[2], req[3])


def give(h, req):
    fid, job, scope, mode = req
    for s in list(h.held.get(job) or ()):
        if s != scope and book.covers(scope, s):
            book.lose(h, job, s)
    book.put(h, job, scope, mode)
    book.unfile(h, req)
    book.recheck(h, job)
    say.grant(h, job, scope, mode)


def settle(h, units):
    seen = {}
    for u in units:
        for fid, req in h.byunit.get(u, {}).items():
            seen[fid] = req
    for fid in sorted(seen, key=lambda f: rankof(h, seen[f])):
        req = seen[fid]
        if fid not in h.line:
            continue
        if grantable(h, req):
            give(h, req)
PYEOF

cat > /app/hold/lift.py <<'PYEOF'
"""Raising a cell ask to the whole unit.

Four cell claims already held in one unit and the next ask in that unit stops being an ask
for a cell: it becomes an ask for the unit, in the strongest mode the job would then need.
The job keeps every one of those cell claims while the raised ask waits, which is the whole
of why a raised ask that is refused can be the thing that closes a loop - it is holding
exactly what the jobs it is waiting for are asking for.
"""
from hold import book, name


def raised(h, job, scope, mode):
    u, c = name.cut(scope)
    if c is None:
        return scope, mode
    pair = h.tally.get(u, {}).get(job)
    if not pair or pair[0] + pair[1] < 5:
        return scope, mode
    out = mode
    if pair[1]:
        out = "w"
    if h.own.get(u, {}).get(job) == "w":
        out = "w"
    return u, book.strongest(out)
PYEOF

cat > /app/hold/knot.py <<'PYEOF'
"""Which jobs can never proceed, and which of them the service gives up on.

A job is held up by another when its ask is refused because that other job holds a
conflicting claim or has a conflicting ask standing ahead of it. Both halves matter: the
refusals by a job that holds nothing at all are exactly the edges a relation drawn over held
claims is missing, and they are what close the short loops.

The search is seeded from the jobs that hold a claim and also have an ask waiting. Every
loop contains one of them: an ask standing ahead of another is filed under a smaller number
inside the same group, so the refusals by waiting asks alone run strictly backwards down the
line and cannot close on themselves. A loop therefore uses at least one refusal by a held
claim, and the job that claim belongs to must have an ask of its own to carry the loop on.
"""
from hold import book, line, name


def blockers(h, job):
    req = h.ask.get(job)
    if req is None:
        return set()
    out = book.whoclash(h, job, req[2], req[3])
    mine = line.rankof(h, req)
    for fid, other in h.byunit.get(name.cut(req[2])[0], {}).items():
        if fid == req[0] or other[1] == job:
            continue
        if not book.overlap(req[2], other[2]) or not book.clash(req[3], other[3]):
            continue
        if line.rankof(h, other) < mine:
            out.add(other[1])
    return out


def loops(h):
    """Every job that following held-up-by can reach from itself."""
    idx, low, onstack, stack, found = {}, {}, {}, [], set()
    count = 0
    for seed in sorted(h.bh, key=lambda j: h.born[j]):
        if seed in idx:
            continue
        idx[seed] = low[seed] = count
        count += 1
        stack.append(seed)
        onstack[seed] = True
        work = [(seed, iter(blockers(h, seed)))]
        while work:
            top, kids = work[-1]
            down = False
            for kid in kids:
                if kid not in idx:
                    idx[kid] = low[kid] = count
                    count += 1
                    stack.append(kid)
                    onstack[kid] = True
                    work.append((kid, iter(blockers(h, kid))))
                    down = True
                    break
                if onstack.get(kid):
                    low[top] = min(low[top], idx[kid])
            if down:
                continue
            work.pop()
            if work:
                up = work[-1][0]
                low[up] = min(low[up], low[top])
            if low[top] == idx[top]:
                part = []
                while True:
                    one = stack.pop()
                    onstack[one] = False
                    part.append(one)
                    if one == top:
                        break
                if len(part) > 1:
                    found.update(part)
    return found


def pick(h, jobs):
    return min(jobs, key=lambda j: (len(h.held.get(j) or ()), -h.born[j]))
PYEOF

cat > /app/hold/turn.py <<'PYEOF'
"""What the service does after an op.

Settling runs only when something was released, because a grant cannot make an ask standing
earlier in the order grantable: it only ever adds or strengthens a claim, and a claim a job
gives up when a whole-unit claim swallows it is covered by that claim. The stall search runs
after every op that could have changed what refuses what - every op that filed an ask, granted
one, or released a claim. An op that changes nothing can create no loop, so it is not asked.
Each cancellation releases claims, which is why it settles and looks again.
"""
from hold import book, knot, line, say


def after(h, units):
    if units:
        line.settle(h, units)
    while True:
        bad = knot.loops(h)
        if not bad:
            return
        gone = knot.pick(h, bad)
        n, where, _had = book.clear(h, gone)
        say.stop(h, gone, n)
        line.settle(h, where)
PYEOF

cat > /app/hold/act.py <<'PYEOF'
"""The four ops.

Order matters here. An ask that is already covered changes nothing and is never filed, so it
cannot be raised either. Raising happens before the refusal test, so what is tested and what
is printed is the whole-unit ask. Settling runs only after something was released, because a
grant cannot make an earlier ask grantable. The stall search runs after every op that filed
an ask or moved a claim, and each cancellation releases claims, which is why it settles and
looks again.
"""
from hold import book, lift, line, name, say, turn


def take(h, job, scope, mode):
    if job in h.ask:
        return
    if book.covered(h, job, scope, mode):
        say.grant(h, job, scope, mode)
        return
    scope, mode = lift.raised(h, job, scope, mode)
    h.nfile += 1
    req = [h.nfile, job, scope, mode]
    book.wake(h, job)
    if line.grantable(h, req):
        line.give(h, req)
    else:
        line.file_(h, req)
    turn.after(h, ())


def drop(h, job, scope):
    gone = book.lose(h, job, scope)
    say.free(h, job, scope, len(h.held.get(job) or ()))
    if not gone:
        return
    book.recheck(h, job)
    book.rest(h, job)
    turn.after(h, (name.cut(scope)[0],))


def over(h, job):
    n, where, had = book.clear(h, job)
    say.over(h, job, n)
    if n or had:
        turn.after(h, where)


def show(h, unit):
    say.show(h, unit, book.listing(h, unit), book.onunit(h, unit))
PYEOF
