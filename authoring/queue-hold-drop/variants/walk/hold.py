from . import bind, line, say


def send(st):
    stuck = set()
    going = []
    for c in st.q:
        if c.sent:
            continue
        nm = line.names(c)
        free = True
        for x in nm:
            if x in stuck:
                free = False
            elif not bind.got(st, x) and not (c.kind == "new" and x == c.a):
                free = False
        if not free:
            stuck.add(line.about(c))
            continue
        going.append(c)
    for c in going:
        c.sent = True
        st.out.append(say.wire("out", c.kind, bind.show(st, c.a)))
