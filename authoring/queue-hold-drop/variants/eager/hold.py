from . import bind, line, say


def send(st):
    stuck = set()
    for c in st.q:
        if c.sent:
            continue
        nm = line.names(c)
        ready = True
        for x in nm:
            if c.kind == "new" and x == c.a:
                continue
            if not bind.got(st, x):
                ready = False
        if ready:
            for x in nm:
                if x in stuck:
                    ready = False
        if not ready:
            stuck.add(line.about(c))
            continue
        c.sent = True
        st.out.append(say.wire("out", c.kind, bind.show(st, c.a)))
