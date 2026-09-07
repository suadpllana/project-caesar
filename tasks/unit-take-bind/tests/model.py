"""Independent model of the binding rules, written against the same contract as the reference.

Different shape on purpose. The reference settles a rank by sweeping every unit and every pull
and keeping the candidates whose cost equals the rank being settled. This model never sweeps:
it holds a heap of pending candidates keyed by rank, pops the whole of the lowest rank at once,
settles those pairs, and then pushes only the candidates the newly settled facts make possible.
Subscriptions stand in for the reference's rescans - one list per source unit for wide pulls,
one per (unit, name) for narrow ones - and a pull whose source name is not yet known to name a
unit waits on that name instead of being re-tried.

Both must agree on every graded program; the agreement is what makes the grading independent of
either implementation. The rules themselves, in the order they bite:

  * a candidate carries a rank and an origin. `own` gives rank 0 at the unit itself; `als`
    gives rank 0 pointing at a unit; a pull gives 1 + the larger of the source reading's rank
    and the rank the name already holds in the source unit.
  * a pull's source name has one reading per unit it can denote: the unit of that name in the
    program at rank 0, and whatever unit the name is bound to in the pulling unit, at that
    binding's rank.
  * a name is settled from its lowest-ranked candidates alone. All of them agreeing on one
    origin binds it; two origins make it a clash, which is terminal and carries nothing onward.
  * `hide` takes a name out of both kinds of pull; `shut` takes it out of wide pulls only.
  * conclusions are drawn in rank order, so nothing settled at rank k can rest on a fact that
    is only settled later.
"""
import heapq

OWN = "own"
UNIT = "unit"
CLASH = "clash"


class Unit:
    __slots__ = ("nm", "owns", "als", "pulls", "shuts", "hides")

    def __init__(self, nm):
        self.nm = nm
        self.owns = []
        self.als = []
        self.pulls = []
        self.shuts = set()
        self.hides = set()


def parse(lines):
    """Program text (one declaration per line) into units plus the ordered ask list."""
    units = {}
    asks = []

    def unit(nm):
        u = units.get(nm)
        if u is None:
            u = units[nm] = Unit(nm)
        return u

    for raw in lines:
        bits = raw.split("#", 1)[0].split()
        if not bits:
            continue
        who, op, args = bits[0], bits[1], bits[2:]
        u = unit(who)
        if op == "own":
            u.owns.append(args[0])
        elif op == "als":
            u.als.append((args[0], args[1]))
        elif op == "pull":
            u.pulls.append((args[0], args[1]))
        elif op == "shut":
            u.shuts.add(args[0])
        elif op == "hide":
            u.hides.add(args[0])
        elif op == "ask":
            asks.append((who, args[0]))
        else:
            raise ValueError("unknown op: %r" % raw)
    return units, asks


def solve(units):
    """Settle every (unit, name) pair, lowest rank first. Returns pair -> (kind, target, rank)."""
    bind = {}
    heap = []
    # A wide pull registers against its source unit; a narrow one against the single pair it
    # wants. Each entry is the rank of the source reading that created it, which is half of a
    # pulled candidate's cost.
    wide = {}
    narrow = {}
    # Pulls whose source name is not (yet) known to name a unit wait here, keyed by that name.
    waiting = {}

    for u in units.values():
        for x in u.owns:
            heapq.heappush(heap, (0, u.nm, x, OWN, u.nm))
        for x, vn in u.als:
            if vn in units:
                heapq.heappush(heap, (0, u.nm, x, UNIT, vn))

    def carry(vn, x, kind, tgt, rank, subs):
        """Push the candidates one settled fact hands to the pulls that subscribe to it."""
        for un, rs in subs:
            heapq.heappush(heap, ((rs if rs > rank else rank) + 1, un, x, kind, tgt))

    def hook(un, s, what, vn, rs):
        """Register one pull under one reading of its source, and drain what is already settled."""
        v = units[vn]
        if what == "*":
            wide.setdefault(vn, []).append((un, rs))
            for x, got in list(bind.items()):
                if x[0] != vn:
                    continue
                kind, tgt, rank = got
                if kind is CLASH or x[1] in v.hides or x[1] in v.shuts:
                    continue
                carry(vn, x[1], kind, tgt, rank, [(un, rs)])
        else:
            narrow.setdefault((vn, what), []).append((un, rs))
            got = bind.get((vn, what))
            if got is not None and got[0] is not CLASH and what not in v.hides:
                carry(vn, what, got[0], got[1], got[2], [(un, rs)])

    for u in units.values():
        for s, what in u.pulls:
            waiting.setdefault((u.nm, s), []).append((u.nm, what))
            if s in units:
                hook(u.nm, s, what, s, 0)

    while heap:
        rank = heap[0][0]
        seen = {}
        while heap and heap[0][0] == rank:
            _, un, x, kind, tgt = heapq.heappop(heap)
            if (un, x) in bind:
                continue
            seen.setdefault((un, x), []).append((kind, tgt))
        for (un, x), cands in seen.items():
            head = cands[0]
            settled = head if all(c == head for c in cands) else (CLASH, None)
            bind[(un, x)] = (settled[0], settled[1], rank)
        for (un, x), got in ((k, bind[k]) for k in seen):
            kind, tgt, _ = got
            if kind is CLASH:
                continue
            u = units[un]
            if x not in u.hides:
                carry(un, x, kind, tgt, rank, narrow.get((un, x), ()))
                if x not in u.shuts:
                    carry(un, x, kind, tgt, rank, wide.get(un, ()))
            if kind is UNIT:
                # The name now denotes a unit inside `un`, so every pull there that used it as
                # its source gains a second reading, at this binding's rank.
                for holder, what in waiting.get((un, x), ()):
                    hook(holder, x, what, tgt, rank)
    return bind


def say(un, x, got):
    if got is None:
        return "%s %s none" % (un, x)
    kind, tgt, rank = got
    if kind is CLASH:
        return "%s %s clash %d" % (un, x, rank)
    return "%s %s %s %s %d" % (un, x, kind, tgt, rank)


def expect(lines):
    units, asks = parse(lines)
    bind = solve(units)
    return [say(un, x, bind.get((un, x))) for un, x in asks]
