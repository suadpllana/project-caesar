from . import bind, line, say


def send(st):
    for c in st.q:
        if c.sent:
            continue
        wait = False
        if c.kind != "new":
            for x in line.names(c):
                if not bind.got(st, x):
                    wait = True
                    break
        if wait:
            continue
        c.sent = True
        st.out.append(say.wire("out", c.kind, bind.show(st, c.a)))
