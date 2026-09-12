"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones the shipped tree exposes at that moment: how many other jobs hold a claim that
conflicts with the ask, how many waiting asks conflict with it, how many of those were filed
earlier, what the job holds here and everywhere, and how long the line is. Nothing about where
an ask stands is offered, because that order is the derivation and the derivation is the task.

The verdict to want is that at least one graded quantity has no short rule. Two should not:
whether an ask is granted, because the asks that refuse it are the ones standing ahead of it
and standing ahead is not filing order, and whether a job is on a loop, because that is
reachability through refusals rather than a count of them. The raise threshold should have a
one-line rule, and does: it is stated in the brief and is not where the work is.

    python3 tools/onelinecheck.py claim-line-stall
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
import gen  # noqa: E402

MODS = ("ops", "hold", "hold.name", "hold.say", "hold.book", "hold.line", "hold.lift",
        "hold.knot", "hold.turn", "hold.act")

ROWS = {"ask-grant": [], "job-loop": [], "ask-raised": []}


def _load():
    here = lab.stage(str(lab.TASK / "solution"))
    sys.path.insert(0, str(here))
    for one in MODS:
        sys.modules.pop(one, None)
    import ops
    from hold import book, knot, lift, line
    return ops, book, knot, lift, line


def _ask_row(h, book, name, req):
    """What the shipped tree shows about one ask at the moment it is decided."""
    job, scope, mode = req[1], req[2], req[3]
    unit = name.cut(scope)[0]
    hit = len(book.whoclash(h, job, scope, mode))
    over = 0
    early = 0
    for fid, other in h.byunit.get(unit, {}).items():
        if other[1] == job:
            continue
        if not book.overlap(scope, other[2]) or not book.clash(mode, other[3]):
            continue
        over += 1
        if fid < req[0]:
            early += 1
    pair = h.tally.get(unit, {}).get(job) or (0, 0)
    return {
        "hit": hit,
        "over": over,
        "early": early,
        "mine": len(h.held.get(job) or ()),
        "here": pair[0] + pair[1],
        "cell": 0 if name.cut(scope)[1] is None else 1,
        "want_w": 1 if mode == "w" else 0,
        "line": len(h.line),
        "on_unit": len(h.byunit.get(unit, ())),
    }


def _job_row(h, book, name, job, bad):
    req = h.ask[job]
    unit = name.cut(req[2])[0]
    hit = len(book.whoclash(h, job, req[2], req[3]))
    over = 0
    for fid, other in h.byunit.get(unit, {}).items():
        if other[1] != job and book.overlap(req[2], other[2]) \
                and book.clash(req[3], other[3]):
            over += 1
    return {
        "hit": hit,
        "over": over,
        "mine": len(h.held.get(job) or ()),
        "born": h.born[job],
        "line": len(h.line),
        "held_here": len(h.own.get(unit, ())) + len(h.tally.get(unit, ())),
        "waiting": len(h.ask),
        "on_unit": len(h.byunit.get(unit, ())),
    }


def samples():
    ops, book, knot, lift, line = _load()
    plain_grant = line.grantable
    plain_loops = knot.loops
    plain_raised = lift.raised
    from hold import name

    state = {"h": None}

    def grantable(h, req):
        out = plain_grant(h, req)
        ROWS["ask-grant"].append((_ask_row(h, book, name, req), bool(out)))
        return out

    def loops(h):
        out = plain_loops(h)
        for job in sorted(h.ask):
            ROWS["job-loop"].append((_job_row(h, book, name, job, out), job in out))
        return out

    def raised(h, job, scope, mode):
        unit, cell = name.cut(scope)
        pair = h.tally.get(unit, {}).get(job) or (0, 0)
        wide = 0
        for one in h.held.get(job) or ():
            if name.cut(one)[1] is not None:
                wide += 1
        out = plain_raised(h, job, scope, mode)
        if cell is not None:
            ROWS["ask-raised"].append(({
                "here": pair[0] + pair[1],
                "anywhere": wide,
                "mine": len(h.held.get(job) or ()),
                "want_w": 1 if mode == "w" else 0,
                "on_unit": len(h.byunit.get(unit, ())),
            }, out[0] == unit))
        return out

    line.grantable = grantable
    knot.loops = loops
    lift.raised = raised
    try:
        for fam, _n, lines in gen.programs("decisions", 12):
            if fam in ("wide", "tall"):
                continue
            h = book.Hold()
            state["h"] = h
            for one in lines:
                ops.ex(h, tuple(one.split()))
    finally:
        line.grantable = plain_grant
        knot.loops = plain_loops
        lift.raised = plain_raised
    return {k: v for k, v in ROWS.items() if v}
