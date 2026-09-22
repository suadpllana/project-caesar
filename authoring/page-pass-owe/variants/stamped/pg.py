"""The page, driven off the view's generator rather than an index into a list."""

from lst import owe
from lst import scr


def serve(st, s):
    sc = st.scrolls[s]
    out = []
    left = sc.c

    while len(out) < sc.n and left > 0:
        i = owe.front(sc)
        if i is None:
            break
        w = st.rows[i][2]
        if w > left and out:
            break
        owe.unowe(st, sc, i)
        scr.gave(sc, i)
        out.append(i)
        left = left - w if w <= left else 0

    over = 0
    for pl in st.view.walk(sc.g, sc.mk):
        if len(out) >= sc.n or left <= 0 or over >= sc.c:
            break
        i = pl[1]
        if scr.had(sc, i):
            scr.looked(sc, pl)
            continue
        w = st.rows[i][2]
        if w <= left:
            scr.looked(sc, pl)
            scr.gave(sc, i)
            out.append(i)
            left -= w
            continue
        if not out:
            scr.looked(sc, pl)
            scr.gave(sc, i)
            out.append(i)
            left = 0
            continue
        if owe.held(st) + w > st.hold:
            break
        scr.looked(sc, pl)
        owe.owe(st, sc, i)
        over += w
    return out
