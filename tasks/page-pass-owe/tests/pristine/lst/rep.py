from lst import owe
from lst import scr


def close(st):
    lines = []
    for s in sorted(st.scrolls):
        sc = st.scrolls[s]
        d = 0
        for pl in st.view.places(sc.g):
            if scr.had(st, sc, pl[1]):
                d += 1
        lines.append((s, d, owe.standing(sc), owe.standing(sc)))
    total = 0
    for i in st.rows:
        if i not in st.got:
            total += st.rows[i][2]
    return lines, total
