"""The step, with a token's placements kept as two parallel lists.

Experts in one list and their slot indices in another, which makes the rank of a placement its
index in either and a loss a pair of truncations.
"""
from lay import back, buf, cap, gate, tally, trim


def _wanted_first(cfg, mbs):
    n = 0
    for s in mbs[0]:
        n += len(gate.want(gate.rank(s), s, cfg.w, ()))
    return n


def _lose(bufs, st, vt, r, last, out, hand):
    """From rank r on the token holds nothing; `hand` leaves rank r to the arrival."""
    experts, slots = st.place[vt]
    for i in range(r + 1 if hand else r, len(experts)):
        bufs.drop(experts[i], slots[i])
    del experts[r:]
    del slots[r:]
    if r == 0:
        st.defer(vt, last, out)


def _admit(cfg, sc, order, bufs, st, tid, last, out):
    wl = gate.want(order[tid], sc[tid], cfg.w, st.blocked[tid])
    st.wl[tid] = wl
    experts, slots = [], []
    st.place[tid] = (experts, slots)
    for e in wl:
        mine = sc[tid][e]
        slot = bufs.free(e)
        if slot is None:
            weak = bufs.weakest(e, st.gone)
            if weak is None or weak[0] >= mine:
                st.refuse(tid, e)
                break
            victim = weak[2]
            seat = weak[1]
            st.gone[victim] = True
            st.refuse(victim, e)
            _lose(bufs, st, victim, st.place[victim][0].index(e), last, out, True)
            bufs.seize(e, seat, tid, mine)
            experts.append(e)
            slots.append(seat)
            continue
        experts.append(e)
        slots.append(bufs.fill(e, tid, mine))
    if wl and not experts:
        st.defer(tid, last, out)


def step(cfg, mbs, out):
    sc = []
    for mb in mbs:
        sc.extend(mb)
    n = len(sc)
    order = [gate.rank(s) for s in sc]

    c = cap.slots(cfg, _wanted_first(cfg, mbs), len(mbs))
    z = cap.budget(cfg, c)
    out.line("cap %d %d" % (c, z))

    st = back.Track(n)
    bufs = buf.Bufs(cfg.ex, c)

    at = 0
    groups = []
    for mb in mbs:
        groups.append(list(range(at, at + len(mb))))
        at += len(mb)
    for m, group in enumerate(groups):
        last = m == len(groups) - 1
        for tid in st.take() + group:
            _admit(cfg, sc, order, bufs, st, tid, last, out)

    trim.shed(cfg, sc, bufs, st, z)
    tally.report(cfg, sc, bufs, st, out, n)
