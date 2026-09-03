"""A second implementation of the panel semantics, written from the specification.

It shares no code with the tree under test. The tree parses into tagged tuples and walks
them with a recursive evaluator; this compiles every expression into a closure once and
calls it. The tree keeps its pending set in a heap ordered by distance; this keeps a plain
set and scans it for the minimum each time. The tree splits the policy across four modules
that the submission replaces; this is one function. Where the two agree, they agree because
the specification says so and not because they share an implementation.

The semantics, restated here so this file can be read on its own:

  A panel has feeds (values written from outside), gauges (values computed from an
  expression over other entries) and latches (attached to an entry).

  DISTANCE. A feed sits at distance 0. A gauge sits one step beyond the deepest entry it
  reads, and one step out if it reads no gauge at all. What a gauge reads is only known
  once it has run, so a gauge that has never run stands provisionally at 1.

  A ROUND. The writes land on their feeds. Every gauge that reads an entry whose value
  moved is pending. While anything is pending, take the pending gauge with the smallest
  distance, and among equals the one declared earliest, and run it. Running it says which
  entries it actually read, which is not necessarily what it read last time: a conditional
  reads one arm or the other. Entries it has stopped reading stop waking it at once, and
  entries it has started reading begin waking it at once.

  TOO EARLY. If a gauge turns out to read a gauge standing at its own distance or beyond,
  it was reached before that entry settled, and the value it produced is discarded and it
  stays pending. Its distance is recorded either way, because the run that says what it
  reads is the run that says where it stands.

  Otherwise the value is committed and recorded. If it moved, every gauge now reading this
  one becomes pending.

  LATCHES. Once the round has gone quiet, every latch whose entry moved during that round
  trips, in the order the panel declares them, at most once each, reporting what its entry
  came to rest at. The writes of the latches that tripped, concatenated in the order they
  tripped, are the next round. Nothing trips while the panel is coming up.

  The build is round 0: every gauge is pending and no latch trips.
"""

STEPS = 60000
TURNS = 60


class Bust(Exception):
    pass


def _split(s):
    out = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == " " or c == ",":
            i += 1
        elif c == "(" or c == ")":
            out.append(c)
            i += 1
        else:
            j = i
            while j < n and s[j] not in " ,()":
                j += 1
            out.append(s[i:j])
            i = j
    return out


def _build(tk, pos):
    """Compile one expression into f(get) -> int, where get(name) records the read."""
    head = tk[pos]
    if head in ("add", "sub", "gt", "eq", "pick"):
        pos += 2
        kids = []
        while tk[pos] != ")":
            k, pos = _build(tk, pos)
            kids.append(k)
        pos += 1
        if head == "add":
            a, b = kids
            return (lambda get: a(get) + b(get)), pos
        if head == "sub":
            a, b = kids
            return (lambda get: a(get) - b(get)), pos
        if head == "gt":
            a, b = kids
            return (lambda get: 1 if a(get) > b(get) else 0), pos
        if head == "eq":
            a, b = kids
            return (lambda get: 1 if a(get) == b(get) else 0), pos
        c, x, y = kids
        return (lambda get: x(get) if c(get) != 0 else y(get)), pos
    try:
        k = int(head)
    except ValueError:
        return (lambda get, _n=head: get(_n)), pos + 1
    return (lambda get, _k=k: _k), pos + 1


def read(text):
    feeds = {}
    code = {}
    lat = []
    turns = []
    order = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line[0] == "#":
            continue
        bits = line.split()
        tag = bits[0]
        if tag == "F":
            feeds[bits[1]] = int(bits[2])
            order.append(bits[1])
        elif tag == "G":
            fn, _ = _build(_split(" ".join(bits[2:])), 0)
            code[bits[1]] = fn
            order.append(bits[1])
        elif tag == "T":
            lat.append((bits[1], bits[2],
                        tuple((w.split("=")[0], int(w.split("=")[1])) for w in bits[3:])))
        elif tag == "R":
            turns.append(tuple((w.split("=")[0], int(w.split("=")[1])) for w in bits[1:]))
        else:
            raise ValueError(tag)
    return feeds, code, lat, turns, order


def solve(text):
    feeds, code, lat, turns, order = read(text)
    ix = {}
    for i, n in enumerate(order):
        ix[n] = i
    isfeed = {}
    val = {}
    for n in order:
        if n in feeds:
            isfeed[n] = True
            val[n] = feeds[n]
        else:
            isfeed[n] = False
            val[n] = 0
    gauges = [n for n in order if not isfeed[n]]
    far = {}
    for n in order:
        far[n] = 0 if isfeed[n] else 1
    reads_of = {}
    for n in gauges:
        reads_of[n] = set()
    log = []
    budget = [0]

    def wakes(entry):
        """Gauges currently reading `entry`, earliest declared first."""
        return sorted((g for g in gauges if entry in reads_of[g]), key=lambda m: ix[m])

    def settle(rno, pend, moved):
        pend = set(pend)
        while pend:
            budget[0] += 1
            if budget[0] > STEPS:
                raise Bust("steps")
            g = min(sorted(pend), key=lambda m: (far[m], ix[m]))
            seen = set()

            def get(name, _s=seen):
                _s.add(name)
                return val[name]

            v = code[g](get)
            reads_of[g] = set(seen)
            early = [d for d in seen if not isfeed[d] and far[d] >= far[g]]
            under = [far[d] for d in seen if not isfeed[d]]
            far[g] = (max(under) + 1) if under else 1
            if early:
                continue
            pend.discard(g)
            old = val[g]
            val[g] = v
            log.append((rno, "cp", g, v))
            if old != v:
                moved.add(g)
                for r in wakes(g):
                    pend.add(r)
        return moved

    settle(0, set(gauges), set())
    rno = 0
    writes = None
    todo = list(turns)
    while todo or writes:
        if writes:
            w = writes
            writes = None
        else:
            w = todo.pop(0)
        rno += 1
        if rno > TURNS:
            raise Bust("turns")
        moved = set()
        for k, v in w:
            if isfeed.get(k) and val[k] != v:
                val[k] = v
                moved.add(k)
                log.append((rno, "in", k, v))
        pend = set()
        for k in sorted(moved, key=lambda m: ix[m]):
            for r in wakes(k):
                pend.add(r)
        settle(rno, pend, moved)
        nxt = []
        for nm, tgt, wr in lat:
            if tgt in moved:
                log.append((rno, "tr", nm, val[tgt]))
                nxt.extend(wr)
        writes = tuple(nxt) if nxt else None
    return {"log": tuple(log),
            "dump": tuple(sorted((n, val[n]) for n in order))}


def check(text):
    """The model's answer for a panel, or None when the panel is not one we grade.

    A panel is well formed when it settles inside the caps and when no gauge has to run
    twice in one round. The second is rare - a gauge that has already run can only be
    reached again if something it reads is pushed further out and then moves afterwards -
    and panels that do it are not graded, so nothing turns on how a submission would order
    that.
    """
    try:
        got = solve(text)
    except Bust:
        return None
    seen = set()
    for rno, tag, name, _v in got["log"]:
        if tag != "cp":
            continue
        if (rno, name) in seen:
            return None
        seen.add((rno, name))
    return got
