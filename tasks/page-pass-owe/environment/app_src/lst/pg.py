from lst import owe
from lst import scr


def serve(st, s):
    sc = st.scrolls[s]
    out = []
    left = sc.c
    for i in list(sc.led):
        if len(out) >= sc.n or left <= 0:
            break
        w = sc.led[i]
        if w <= left:
            owe.unowe(st, sc, i)
            scr.gave(st, sc, i)
            out.append(i)
            left -= w
    v, at = st.view.start(sc.g, sc.mk)
    while len(out) < sc.n and left > 0:
        if at >= len(v):
            break
        pl = v[at]
        at += 1
        i = pl[1]
        if scr.had(st, sc, i):
            scr.looked(sc, pl)
            continue
        w = st.rows[i][2]
        if w > left:
            break
        scr.looked(sc, pl)
        scr.gave(st, sc, i)
        out.append(i)
        left -= w
    return out
