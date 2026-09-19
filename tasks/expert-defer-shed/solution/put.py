"""The step: capacity, then the microbatch queues, then the shed, then the report.

A token is placed at the experts of its want list in rank order and stops at the first one it
cannot enter, so what it holds is always a prefix of that list. That is what makes a loss
total below the rank it happened at: the placements after it would no longer be a prefix, so
they go too, and their slots are free for whatever arrives next.

A full expert is not a closed door. The weakest occupant that has not already been displaced
this step leaves if the arrival outscores it there, and the arrival takes that exact slot
rather than the lowest free one, because the slot never became free.
"""
from lay import back, buf, cap, gate, tally, trim


def _ids(mbs):
    base = 0
    out = []
    for mb in mbs:
        out.append(list(range(base, base + len(mb))))
        base += len(mb)
    return out


def _first_wanted(cfg, mbs):
    """The wanted slots of the first microbatch, which is what the buffers are sized from."""
    if not mbs:
        return 0
    n = 0
    for weight in mbs[0]:
        n += len(gate.want(gate.rank(weight), weight, cfg.w, ()))
    return n


def _oust(bufs, st, weights, vt, e, last, out):
    """Take e away from vt, and with it every placement vt holds at a later rank."""
    where = st.place[vt]
    r = 0
    while where[r][0] != e:
        r += 1
    for ee, ss in where[r + 1:]:
        bufs.drop(ee, ss)
    st.place[vt] = where[:r]
    st.gone[vt] = True
    st.refuse(vt, e)
    if r == 0:
        st.defer(vt, last, out)


def _admit(cfg, weights, order, bufs, st, token, last, out):
    wl = gate.want(order[token], weights[token], cfg.w, st.blocked[token])
    st.wl[token] = wl
    held = []
    for e in wl:
        weight = weights[token][e]
        slot = bufs.free(e)
        if slot is None:
            weak = bufs.weakest(e, st.gone)
            if weak is None or weak[0] >= weight:
                st.refuse(token, e)
                break
            _oust(bufs, st, weights, weak[2], e, last, out)
            bufs.seize(e, weak[1], token, weight)
            held.append((e, weak[1]))
            continue
        held.append((e, bufs.fill(e, token, weight)))
    st.place[token] = held
    if wl and not held:
        st.defer(token, last, out)


def step(cfg, mbs, out):
    weights = []
    for mb in mbs:
        weights.extend(mb)
    n = len(weights)
    order = [gate.rank(weight) for weight in weights]

    c = cap.slots(cfg, _first_wanted(cfg, mbs), len(mbs))
    z = cap.budget(cfg, c)
    out.line("cap %d %d" % (c, z))

    st = back.Track(n)
    bufs = buf.Bufs(cfg.ex, c)

    groups = _ids(mbs)
    for m, group in enumerate(groups):
        last = m == len(groups) - 1
        for token in st.take() + group:
            _admit(cfg, weights, order, bufs, st, token, last, out)

    trim.shed(cfg, weights, bufs, st, z)
    tally.report(cfg, weights, bufs, st, out, n)
