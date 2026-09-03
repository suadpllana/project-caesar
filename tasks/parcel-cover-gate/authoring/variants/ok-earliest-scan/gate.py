from base import tape, wire

from bay import desc, stand


def given(st, w, no):
    wire.held(st, w).append(no)


def gate(st, w):
    view = tape.seat(st, w)
    bag = wire.held(st, w)
    got = set()
    while True:
        pick = -1
        for at in range(len(bag)):
            if stand.ripe(st, st.parc[bag[at] - 1], view):
                pick = at
                break
        if pick < 0:
            return got
        p = st.parc[bag.pop(pick) - 1]
        for s in p:
            v = p[s]
            cur = view.get(s, -1)
            if cur != v and (cur == -1 or desc.runs(st, v, cur)):
                view[s] = v
                got.add(s)
