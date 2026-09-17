from . import bind, lay, line, say, view


def sweep(st, at, seed):
    doomed = []
    for i in range(at, len(st.q)):
        c = st.q[i]
        if seed.intersection(line.names(c)):
            seed.add(line.about(c))
            doomed.append(i)
    for i in reversed(doomed):
        st.q.pop(i)
    return len(doomed)


def answer(st, good):
    i = line.waiting(st)
    if i < 0:
        st.out.append("idle")
        return
    c = st.q.pop(i)
    if not good:
        st.out.append("gone %d" % (1 + sweep(st, i, {line.about(c)})))
        view.fresh(st)
        return
    lay.one(st.base, c)
    if c.kind == "new":
        bind.hand(st, c.a)
    st.out.append(say.wire("ack", c.kind, bind.show(st, c.a)))
    view.fresh(st)
