"""The step, driven from a dict of what each token holds."""
from lay import back, buf, cap, gate, tally, trim


def _lose(bufs, st, vt, r, last, out, hand):
    row = st.held(vt)
    for e, slot in row[r + 1 if hand else r:]:
        bufs.drop(e, slot)
    del row[r:]
    if r == 0:
        st.defer(vt, last, out)


def _admit(cfg, sc, order, bufs, st, tid, last, out):
    wl = gate.want(order[tid], sc[tid], cfg.w, st.blocked[tid])
    st.wl[tid] = wl
    row = st.held(tid)
    del row[:]
    for e in wl:
        mine = sc[tid][e]
        slot = bufs.free(e)
        if slot is None:
            weak = bufs.weakest(e, st.gone)
            if weak is None or weak[0] >= mine:
                st.refuse(tid, e)
                break
            st.gone[weak[2]] = True
            st.refuse(weak[2], e)
            seats = st.held(weak[2])
            _lose(bufs, st, weak[2], [p[0] for p in seats].index(e), last, out, True)
            bufs.seize(e, weak[1], tid, mine)
            row.append((e, weak[1]))
            continue
        row.append((e, bufs.fill(e, tid, mine)))
    if wl and not row:
        st.defer(tid, last, out)


def step(cfg, mbs, out):
    sc = []
    for mb in mbs:
        sc.extend(mb)
    n = len(sc)
    order = [gate.rank(s) for s in sc]

    first = 0
    for s in mbs[0]:
        first += len(gate.want(gate.rank(s), s, cfg.w, ()))
    c = cap.slots(cfg, first, len(mbs))
    z = cap.budget(cfg, c)
    out.line("cap %d %d" % (c, z))

    st = back.Track(n)
    bufs = buf.Bufs(cfg.ex, c)
    for tid in range(n):
        st.held(tid)

    at = 0
    bounds = []
    for mb in mbs:
        bounds.append((at, at + len(mb)))
        at += len(mb)
    for m, (lo, hi) in enumerate(bounds):
        last = m == len(bounds) - 1
        for tid in st.take() + list(range(lo, hi)):
            _admit(cfg, sc, order, bufs, st, tid, last, out)

    trim.shed(cfg, sc, bufs, st, z)
    tally.report(cfg, sc, bufs, st, out, n)
