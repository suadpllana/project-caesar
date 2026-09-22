#!/bin/bash
# every argument is bound before any candidate is judged
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
from res import best, cost, pick, pin, spec


class State:
    def __init__(self, prog):
        self.prog = prog
        self.pins = {}
        self.sum = 0
        self.why = "none"


def new(prog):
    return State(prog)


def total(state):
    return state.sum


def ask(state, node):
    state.why = "none"
    binds = []
    made = []
    gives = walk(state, node, None, binds, made)
    if gives is None:
        return spec.Result(state.why, None, [], [])
    return spec.Result("bind", gives, binds, made)


def walk(state, node, expected, binds, made):
    prog = state.prog
    stands = []
    for arg in node.args:
        if arg.args is None:
            stands.append(prog.vals[arg.name])
        else:
            got = walk(state, arg, None, binds, made)
            if got is None:
                return None
            stands.append(got)
    rows = []
    keep = []
    for ent in pick.cands(prog, node.name, len(node.args)):
        row = fit(state, ent, stands, made)
        if row is None:
            continue
        gives = pick.result(ent, state.pins.get(ent.idx))
        last = cost.result(prog, gives, expected)
        if last is None:
            continue
        rows.append(row + [last])
        keep.append((ent, gives))
    if not rows:
        state.why = "none"
        return None
    which = best.winner(rows)
    if which is None:
        state.why = "amb"
        return None
    ent, gives = keep[which]
    binds.append((node.site, ent.idx))
    state.sum += sum(rows[which])
    return gives


def fit(state, ent, stands, made):
    prog = state.prog
    settled = state.pins.get(ent.idx) if ent.opened else None
    if ent.opened and settled is None:
        spots = pick.opens(ent)
        if not spots:
            return None
        settled = pin.settle(prog, [stands[i] for i in spots])
        if settled is None or not pick.in_bound(prog, ent, settled):
            return None
        state.pins[ent.idx] = settled
        made.append((ent.idx, settled))
    row = []
    for asked, was in zip(pick.slots(ent, settled), stands):
        step = cost.slot(prog, was, asked)
        if step is None:
            return None
        row.append(step)
    return row
PYEOF
