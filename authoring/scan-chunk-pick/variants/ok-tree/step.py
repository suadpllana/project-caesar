"""Deciding one chunk for one condition, and what a read settles.

The chunk's statistics and its dictionary describe the chunk as written, and a row with an
update no longer takes its value from it. So a pair is decided in two halves: the live rows
carrying an update are tested on their new value, which costs nothing, and only the rest are
put to the header, then to a usable dictionary, then to a read. When nothing alive still takes
its value from the chunk the second half is empty and nothing is consulted or read.

A read settles every condition of the query over that column, counted over the chunk as
written, not just the one that asked for it: from then on those conditions are estimated on
this chunk by an exact count rather than by the header.
"""
from scn import dct, hdr, live, rd


def load(seg, q, st, ch, out):
    out.dc(ch.c, ch.j)
    vals = rd.values(ch)
    st.vals[(ch.c, ch.j)] = vals
    for cd in q.conds:
        if cd.c == ch.c:
            t = 0
            for v in vals:
                if rd.sat(cd, v):
                    t += 1
            st.hit[(ch.c, ch.j, cd.pos)] = t
    st.dirty.add((ch.c, ch.j))
    return vals


def decide(seg, q, st, cond, j, out):
    c = cond.c
    ch = seg.cols[c][j]
    up = seg.up[c]
    held, moved = live.split(st, c, j)
    dead = [r for r in moved if not rd.sat(cond, up[r])]
    if held:
        dead.extend(_held(seg, q, st, cond, ch, held, out))
    live.kill(st, dead)


def _held(seg, q, st, cond, ch, held, out):
    if hdr.miss(seg, ch, cond):
        return held
    if hdr.allsat(seg, ch, cond):
        return []
    vals = st.vals.get((ch.c, ch.j))
    if vals is None:
        if cond.kind not in ("nn", "nu") and dct.usable(ch):
            verdict = dct.decide(seg, ch, cond, st, out)
            if verdict == "drop":
                return held
            if verdict == "keep":
                return []
        vals = load(seg, q, st, ch, out)
    s = ch.start
    return [r for r in held if not rd.sat(cond, vals[r - s])]
