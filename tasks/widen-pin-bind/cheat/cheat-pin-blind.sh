#!/bin/bash
# a pin made at one slot is not in force at the slots after it
set -euo pipefail

cat > /app/res/kind.py <<'PYEOF'
"""The rise graph. `steps` is the only thing anyone asks it for.

A kind rises to another when a chain of declared `rise` edges leads from the first to the
second, and the number the binder wants is the length of the shortest such chain. Two chains
of different lengths between the same pair are ordinary in a declaration set that has grown,
and the shorter one is the answer: the cost of a slot is how far the argument had to travel,
not how far some walk of the graph happened to go.
"""
from collections import deque


def steps(prog, a, b):
    """Shortest number of rise edges from `a` up to `b`, 0 for the same kind, None if none."""
    if a == b:
        return 0
    seen = {a}
    queue = deque([(a, 0)])
    while queue:
        cur, far = queue.popleft()
        for nxt in prog.ups.get(cur, ()):
            if nxt == b:
                return far + 1
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, far + 1))
    return None
PYEOF

cat > /app/res/pick.py <<'PYEOF'
"""Which entries a call can mean, and what their slots ask for once the open kind is known.

Candidates are the entries that carry the call's name and take exactly as many slots as the
call has arguments. Nothing here judges them: the arity filter is the whole of it, and an
entry that cannot take its arguments is dropped later, by the trial that tries it.
"""
from res import kind


def cands(prog, name, count):
    """Entries named `name` taking `count` slots, in declaration order."""
    return [ent for ent in prog.entries
            if ent.name == name and len(ent.params) == count]


def opens(ent):
    """The positions of the entry's open slots."""
    return [i for i, p in enumerate(ent.params) if p == "*"]


def slots(ent, settled):
    """The kinds the entry's slots ask for, with the open kind put in."""
    return [settled if p == "*" else p for p in ent.params]


def result(ent, settled):
    """The kind the entry gives back, with the open kind put in."""
    return settled if ent.ret == "*" else ent.ret


def in_bound(prog, ent, settled):
    """An open entry may only be settled at a kind that rises to its bound."""
    return kind.steps(prog, settled, ent.bound) is not None
PYEOF

cat > /app/res/pin.py <<'PYEOF'
"""Settling the open kind of an entry that has not been pinned yet.

Every open slot contributes the kind its argument stands at, and the entry is settled at the
one kind all of them rise to that rises to every other kind all of them rise to. That is a
stronger demand than picking the nearest common one: where two common kinds sit side by side
with neither rising to the other, there is no answer and the entry drops out of the call.
"""
from res import kind


def settle(prog, sources):
    """The single least kind every source rises to, or None when there is not exactly one."""
    over = [k for k in prog.kinds
            if all(kind.steps(prog, s, k) is not None for s in sources)]
    for k in over:
        if all(kind.steps(prog, k, other) is not None for other in over):
            return k
    return None
PYEOF

cat > /app/res/cost.py <<'PYEOF'
"""The numbers a trial is judged on.

A slot costs the steps from the kind its argument stands at to the kind the slot asks for.
The last number of the vector is the same measure taken on the way out: from the kind the
entry gives back to the kind the call was asked for, and nothing when it was asked for
nothing. Every language keeps the result out of this comparison; here it is the last
component of the same vector and decides calls that tie on every argument.
"""
from res import kind


def slot(prog, stands, asked):
    """What an argument standing at `stands` costs in a slot asking for `asked`."""
    return kind.steps(prog, stands, asked)


def result(prog, gives, expected):
    """What the entry's result costs against the kind the call was asked for."""
    if expected is None:
        return 0
    return kind.steps(prog, gives, expected)
PYEOF

cat > /app/res/best.py <<'PYEOF'
"""Choosing between the trials that survived.

The rule is a comparison and not a total: an entry wins by being no worse than each other
survivor at every number of the vector and better at one of them. Two vectors that cross -
cheaper at one slot, dearer at another - leave neither able to beat the other, and the call is
ambiguous however the two totals compare. A single survivor wins with nothing to beat.
"""


def beats(a, b):
    """True when vector `a` is no worse than `b` everywhere and better somewhere."""
    return all(x <= y for x, y in zip(a, b)) and any(x < y for x, y in zip(a, b))


def winner(vecs):
    """The index of the vector that beats every other, or None when no vector does."""
    for i, a in enumerate(vecs):
        if all(beats(a, b) for j, b in enumerate(vecs) if j != i):
            return i
    return None
PYEOF

cat > /app/res/walk.py <<'PYEOF'
"""Binding a call, and everything that survives it.

Three things make this more than a recursive walk over the expression.

A call in a slot is bound against the kind that slot asks for, and the kind it gives back is
compared with that same kind, so the same call binds to different entries under different
candidates of the call above it. Nothing can be bound bottom up: an argument has no kind
until a candidate supplies one.

A trial that is abandoned or beaten leaves nothing behind. An entry pinned while a slot was
being tried is pinned only for the rest of that trial; when the trial loses, the pin goes
with it. So pins are carried as a map threaded through the trial rather than written into the
state, and only the winning trial's pins are handed back to the caller, in the order they were
made - which is not slot order, because the open slots of an unpinned entry are bound before
the rest.

The same call is tried again under every candidate of the call above it, which is exponential
in nesting depth and is what the deep programs are for. What a call produces depends on the
call, the kind it was asked for and the pins in force and on nothing else, so the three of
them are the memo key. Keying on the first two alone answers a trial from a world that was
thrown away, and keying on the site number rather than the call answers one expression from
another, because sites are numbered inside their own expression and the numbers repeat.
"""
from res import best, cost, pick, pin, spec


class Out:
    """What a site produced: its result, the tree it bound, the pins it would leave."""

    def __init__(self, how, kind=None, binds=None, pins=None, total=0, vec=None):
        self.how = how
        self.kind = kind
        self.binds = binds if binds is not None else []
        self.pins = pins if pins is not None else []
        self.total = total
        self.vec = vec if vec is not None else []


class State:
    def __init__(self, prog):
        self.prog = prog
        self.pins = {}
        self.sum = 0
        self.memo = {}


def new(prog):
    return State(prog)


def total(state):
    return state.sum


def ask(state, node):
    """One top-level expression: bind it, then keep what the winning trial left."""
    out = bind(state, node, None, state.pins)
    if out.how != "bind":
        return spec.Result(out.how, None, [], [])
    for ent, settled in out.pins:
        state.pins[ent] = settled
    state.sum += out.total
    return spec.Result("bind", out.kind, out.binds, out.pins)


def bind(state, node, expected, pins):
    key = (id(node), expected, tuple(sorted(pins.items())))
    got = state.memo.get(key)
    if got is None:
        got = choose(state, node, expected, pins)
        state.memo[key] = got
    return got


def choose(state, node, expected, pins):
    """Try every candidate from the same pins, then compare the survivors."""
    trials = []
    for ent in pick.cands(state.prog, node.name, len(node.args)):
        one = trial(state, node, ent, expected, pins)
        if one is not None:
            trials.append(one)
    if not trials:
        return Out("none")
    which = best.winner([one.vec for one in trials])
    if which is None:
        return Out("amb")
    return trials[which]


def trial(state, node, ent, expected, pins):
    """One candidate, on its own layer of pins. None when it cannot take the call."""
    prog = state.prog
    here = dict(pins)
    under = [[] for _ in node.args]
    made = []
    took = [None] * len(node.args)
    total = 0
    settled = here.get(ent.idx) if ent.opened else None
    fresh = None

    if ent.opened and settled is None:
        spots = pick.opens(ent)
        if not spots:
            return None
        sources = []
        for i in spots:
            arg = node.args[i]
            if arg.args is None:
                sources.append(prog.vals[arg.name])
                continue
            sub = bind(state, arg, None, here)
            if sub.how != "bind":
                return None
            made.extend(sub.pins)
            under[i] = sub.binds
            total += sub.total
            sources.append(sub.kind)
        settled = pin.settle(prog, sources)
        if settled is None or not pick.in_bound(prog, ent, settled):
            return None
        for i, stands in zip(spots, sources):
            took[i] = cost.slot(prog, stands, settled)
        fresh = (ent.idx, settled)

    asks = pick.slots(ent, settled)
    for i, arg in enumerate(node.args):
        if took[i] is not None:
            continue
        want = asks[i]
        if arg.args is None:
            paid = cost.slot(prog, prog.vals[arg.name], want)
        else:
            sub = bind(state, arg, want, here)
            if sub.how != "bind":
                return None
            made.extend(sub.pins)
            under[i] = sub.binds
            total += sub.total
            paid = cost.slot(prog, sub.kind, want)
        if paid is None:
            return None
        took[i] = paid

    gives = pick.result(ent, settled)
    back = cost.result(prog, gives, expected)
    if back is None:
        return None
    vec = took + [back]
    if fresh is not None:
        made.append(fresh)
    binds = [(node.site, ent.idx)]
    for part in under:
        binds.extend(part)
    return Out("bind", kind=gives, binds=binds, pins=made,
               total=total + sum(vec), vec=vec)
PYEOF
