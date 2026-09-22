"""The closing report, walking the view's id generator."""

from lst import owe


def close(st):
    lines = []
    total = 0
    for s in sorted(st.scrolls):
        sc = st.scrolls[s]
        u = 0
        for i in st.view.members(sc.g):
            if i not in sc.got:
                u += 1
        lines.append((s, len(sc.got), owe.standing(sc), u))
        total += owe.weight(sc)
    return lines, total
