"""Correct variant: the pending pairs are held in one list and scanned from it."""
from scn import hdr, live, step


def run(seg, q, st, out):
    pairs = []
    for cd in q.conds:
        for ch in seg.cols[cd.c]:
            pairs.append((cd, ch))
    while True:
        low = None
        pick = None
        for cd, ch in pairs:
            if ch.j in st.done[cd.pos]:
                continue
            have = live.count(st, cd.c, ch.j)
            if have <= 0:
                continue
            seen = st.hit.get((cd.c, ch.j, cd.pos))
            if seen is None:
                seen = hdr.guess(seg, ch, cd)
            score = min(have, seen)
            if low is None or score < low:
                low = score
                pick = (cd, ch)
        if pick is None:
            return
        cd, ch = pick
        step.decide(seg, q, st, cd, ch.j, out)
        st.done[cd.pos].add(ch.j)
