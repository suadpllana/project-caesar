"""A correct binder that keeps one pin table and rolls it back.

The reference threads a fresh map of pins through every trial. This one keeps a single table
with an undo log: a trial applies what its slots pin, and puts it all back when it ends,
whether it was abandoned, beaten or kept - the kept one's pins are applied again by the call
above it. The memo is keyed by a version that moves whenever the table moves, rather than by
the pins themselves, so a world that has been left and come back to reads as a new one and
loses hits it could have kept. That costs time and never an answer.
"""
from res import best, cost, pick, pin, spec


class Out:
    def __init__(self, how, kind=None, binds=None, pins=None, total=0, vec=None):
        self.how = how
        self.kind = kind
        self.binds = binds or []
        self.pins = pins or []
        self.total = total
        self.vec = vec or []


class State:
    def __init__(self, prog):
        self.prog = prog
        self.pins = {}
        self.sum = 0
        self.memo = {}
        self.age = 0


def new(prog):
    return State(prog)


def total(state):
    return state.sum


def apply(state, pairs, log=None):
    for ent, settled in pairs:
        state.pins[ent] = settled
        state.age += 1
        if log is not None:
            log.append(ent)


def undo(state, log):
    for ent in reversed(log):
        del state.pins[ent]
        state.age += 1
    del log[:]


def ask(state, node):
    out = bind(state, node, None)
    if out.how != "bind":
        return spec.Result(out.how, None, [], [])
    apply(state, out.pins)
    state.sum += out.total
    return spec.Result("bind", out.kind, out.binds, out.pins)


def bind(state, node, expected):
    key = (id(node), expected, state.age)
    if key in state.memo:
        return state.memo[key]
    alive = []
    for ent in pick.cands(state.prog, node.name, len(node.args)):
        one = trial(state, node, ent, expected)
        if one is not None:
            alive.append(one)
    if not alive:
        out = Out("none")
    else:
        which = best.winner([one.vec for one in alive])
        out = Out("amb") if which is None else alive[which]
    state.memo[key] = out
    return out


def trial(state, node, ent, expected):
    prog = state.prog
    log = []
    under = [[] for _ in node.args]
    made = []
    took = [None] * len(node.args)
    deep = 0
    settled = state.pins.get(ent.idx) if ent.opened else None
    mine = None

    if ent.opened and settled is None:
        spots = pick.opens(ent)
        if not spots:
            return None
        stands = []
        for i in spots:
            arg = node.args[i]
            if arg.args is None:
                stands.append(prog.vals[arg.name])
                continue
            sub = bind(state, arg, None)
            if sub.how != "bind":
                undo(state, log)
                return None
            apply(state, sub.pins, log)
            made.extend(sub.pins)
            under[i] = sub.binds
            deep += sub.total
            stands.append(sub.kind)
        settled = pin.settle(prog, stands)
        if settled is None or not pick.in_bound(prog, ent, settled):
            undo(state, log)
            return None
        for i, was in zip(spots, stands):
            took[i] = cost.slot(prog, was, settled)
        mine = (ent.idx, settled)

    asks = pick.slots(ent, settled)
    for i, arg in enumerate(node.args):
        if took[i] is not None:
            continue
        if arg.args is None:
            paid = cost.slot(prog, prog.vals[arg.name], asks[i])
        else:
            sub = bind(state, arg, asks[i])
            if sub.how != "bind":
                undo(state, log)
                return None
            apply(state, sub.pins, log)
            made.extend(sub.pins)
            under[i] = sub.binds
            deep += sub.total
            paid = cost.slot(prog, sub.kind, asks[i])
        if paid is None:
            undo(state, log)
            return None
        took[i] = paid

    gives = pick.result(ent, settled)
    back = cost.result(prog, gives, expected)
    undo(state, log)
    if back is None:
        return None
    vec = took + [back]
    if mine is not None:
        made = made + [mine]
    binds = [(node.site, ent.idx)]
    for part in under:
        binds.extend(part)
    return Out("bind", kind=gives, binds=binds, pins=made, total=deep + sum(vec), vec=vec)
