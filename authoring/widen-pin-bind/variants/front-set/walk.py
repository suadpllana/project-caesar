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
    key = (id(node), expected, frozenset(pins.items()))
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
            for idx, was in sub.pins:
                here[idx] = was
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
            for idx, was in sub.pins:
                here[idx] = was
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
