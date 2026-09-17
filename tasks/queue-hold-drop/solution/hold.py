from . import bind, line, say


def send(st):
    held = set()
    for c in st.q:
        if c.sent:
            continue
        nm = line.names(c)
        wait = False
        for x in nm:
            if c.kind == "new" and x == c.a:
                continue
            if not bind.got(st, x):
                wait = True
                break
        if wait or held.intersection(nm):
            held.add(line.about(c))
            continue
        c.sent = True
        st.out.append(say.wire("out", c.kind, bind.show(st, c.a)))
