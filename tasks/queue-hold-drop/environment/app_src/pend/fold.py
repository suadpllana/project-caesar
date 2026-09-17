from . import bind, lay, line, say


def sweep(st, at, seed):
    keep = st.q[:at]
    took = 0
    for c in st.q[at:]:
        if seed.intersection(line.names(c)):
            took += 1
        else:
            keep.append(c)
    st.q = keep
    return took


def answer(st, good):
    i = line.waiting(st)
    if i < 0:
        st.out.append("idle")
        return
    c = st.q.pop(i)
    if good:
        lay.one(st.base, c)
        ident = bind.show(st, c.a)
        if c.kind == "new":
            bind.hand(st, c.a)
        st.out.append(say.wire("ack", c.kind, ident))
    else:
        st.out.append("gone %d" % (1 + sweep(st, i, {line.about(c)})))
