"""The frame for the ok-memo variant: a while loop over an explicit pass counter."""
from view import lay, pick, stick


def start(v):
    lay.start(v)
    v.saved = None


def before(v):
    band = stick.band(v, v.s)
    got = pick.first(v, v.s, band)
    if got is None:
        v.saved = None
        return
    line = v.s + band
    saved = []
    while got is not None:
        saved.append((got, lay.top(v, got) - line))
        got = got.par
    v.saved = saved


def after(v):
    last_to = None
    live = False
    for kind, b, arg in v.log:
        if kind == "to":
            last_to = arg
        else:
            x = b
            while x is not None and not live:
                live = x.live
                x = x.par
    lay.repair(v)
    most = max(0, lay.doc_height(v) - v.vh)

    def fit(x):
        return x if 0 <= x <= most else (0 if x < 0 else most)

    if last_to is not None:
        return fit(last_to), "off scroll"
    if live:
        return fit(v.s), "off live"
    if v.saved is None:
        return fit(v.s), "none"
    at, count, reached = v.s, 0, []
    while count < 4:
        count += 1
        band = stick.band(v, at)
        holder = None
        for box, gap in v.saved:
            if lay.in_flow(box) and lay.height(v, box) > 0 and not stick.over(v, box, at):
                holder = (box, gap)
                break
        if holder is None:
            return fit(at), "none"
        box, gap = holder
        goal = fit(lay.top(v, box) - gap - band)
        if goal == at:
            return at, box.id
        reached.append((goal, count, box))
        at = goal
    goal, _count, box = sorted(reached, key=lambda r: (r[0], r[1]))[0]
    return goal, box.id
