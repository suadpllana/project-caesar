"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones available where the decision is made: how many candidates survived, where the lowest
total sits, where the lexicographic minimum sits, how many kinds the open slots stand at and
where the first and the highest of them sit in declaration order. Nothing says which candidate
is no worse everywhere and better somewhere, and nothing says which kind every source rises to,
because those are the answers rather than the inputs.

The verdict to want is that at least one graded quantity has no short rule. Two should not: the
winner, because it is a comparison between vectors and not a place in an order, and the settled
kind, because it is the least common kind rather than one of the kinds the slots stand at. The
watched functions are the reference's own, called through the tree the reference is laid over,
and the run asserts it still reproduces the sealed model on every program, so a drifted copy
cannot quietly report on a different binder.

    python3 tools/onelinecheck.py widen-pin-bind
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

ROWS = {"winner": [], "settled": [], "trial-kept": [], "slot-cost": []}


def _install(here):
    sys.path.insert(0, str(here))
    for name in [n for n in list(sys.modules)
                 if n == "run_bind" or n == "res" or n.startswith("res.")]:
        del sys.modules[name]
    import run_bind
    from res import best, cost, kind, pin, walk
    return run_bind, best, cost, kind, pin, walk


def _watch(best, cost, kind, pin, walk):
    real_winner = best.winner
    real_settle = pin.settle
    real_slot = cost.slot
    real_choose = walk.choose

    def winner(vecs):
        got = real_winner(vecs)
        sums = [sum(v) for v in vecs]
        low = min(sums)
        ROWS["winner"].append(({
            "n": len(vecs),
            "lowsum": sums.index(low),
            "lowlex": vecs.index(min(vecs)),
            "ties": sums.count(low),
            "width": len(vecs[0]),
        }, got if got is not None else -1))
        return got

    def settle(prog, sources):
        got = real_settle(prog, sources)
        order = {k: i for i, k in enumerate(prog.kinds)}
        high = sources[0]
        for one in sources[1:]:
            if kind.steps(prog, high, one) is not None:
                high = one
        ROWS["settled"].append(({
            "srcs": len(sources),
            "distinct": len(set(sources)),
            "first": order[sources[0]],
            "high": order[high],
            "kinds": len(prog.kinds),
        }, order[got] if got is not None else -1))
        return got

    def slot(prog, stands, asked):
        got = real_slot(prog, stands, asked)
        if got is not None:
            ROWS["slot-cost"].append(({
                "same": 1 if stands == asked else 0,
                "edge": 1 if asked in prog.ups.get(stands, ()) else 0,
                "outdeg": len(prog.ups.get(stands, ())),
                "indeg": sum(1 for k in prog.kinds if asked in prog.ups.get(k, ())),
            }, got))
        return got

    def choose(state, node, expected, pins):
        out = real_choose(state, node, expected, pins)
        cands = len(walk.pick.cands(state.prog, node.name, len(node.args)))
        if out.how == "bind":
            ROWS["trial-kept"].append(({
                "cands": cands,
                "args": len(node.args),
                "pins": len(out.pins),
                "asked": 0 if expected is None else 1,
                "total": min(out.total, 9),
            }, 1 if out.pins else 0))
        return out

    best.winner = winner
    pin.settle = settle
    cost.slot = slot
    walk.choose = choose


def samples():
    cases, gen, model = lab.sealed()
    here = lab.tree(lab.SOL)
    run_bind, best, cost, kind, pin, walk = _install(here)
    _watch(best, cost, kind, pin, walk)
    work = [cases.prog(name) for name in cases.ORDER]
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(6):
            work.append(gen.build(fam, random.Random("decide|%s|%d" % (fam, i))))
    for lines in work:
        got = run_bind.run("\n".join(lines) + "\n")
        assert got == model.expect(lines), "the watched copy drifted from the sealed model"
    return ROWS
