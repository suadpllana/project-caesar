from base import tape, wire

from bay import desc, stand


def given(st, w, no):
    wire.held(st, w).append(no)


def gate(st, w):
    view = tape.seat(st, w)
    bag = wire.held(st, w)
    got = set()
    for no in bag:
        p = st.parc[no - 1]
        if not stand.ripe(st, p, view):
            continue
        for s in p:
            v = p[s]
            cur = view.get(s, -1)
            if cur != v and desc.runs(st, v, cur):
                view[s] = v
                got.add(s)
    del bag[:]
    return got
