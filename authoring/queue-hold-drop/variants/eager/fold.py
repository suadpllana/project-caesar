from . import bind, lay, line, say, view


def sweep(st, at, seed):
    left = st.q[:at]
    took = 0
    for c in st.q[at:]:
        hit = False
        for x in line.names(c):
            if x in seed:
                hit = True
        if hit:
            seed.add(line.about(c))
            took += 1
        else:
            left.append(c)
    st.q = left
    return took


def answer(st, good):
    at = line.waiting(st)
    if at < 0:
        st.out.append("idle")
        return
    c = st.q.pop(at)
    if good:
        lay.one(st.base, c)
        if c.kind == "new":
            bind.hand(st, c.a)
        st.out.append(say.wire("ack", c.kind, bind.show(st, c.a)))
    else:
        took = sweep(st, at, {line.about(c)})
        st.out.append("gone %d" % (took + 1))
    view.fresh(st)
