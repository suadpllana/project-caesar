from scn import dct, hdr, rd


def read_chunk(seg, st, ch, out, conds_by_col, exact_cache):
    """Ensure the chunk has been read this query; return its raw (as
    written) values. Also settles the exact count, over the chunk as
    written, of every condition of the query sharing this column -- a read
    fixes all of them at once, per the spec."""
    key = (ch.c, ch.j)
    vals = st.vals.get(key)
    if vals is not None:
        return vals
    out.dc(ch.c, ch.j)
    vals = rd.values(ch)
    st.vals[key] = vals
    conds = conds_by_col.get(ch.c)
    if conds:
        for cd in conds:
            t = 0
            for v in vals:
                if rd.sat(cd, v):
                    t += 1
            exact_cache[(cd.pos, ch.j)] = t
    return vals


def apply_pair(seg, st, cd, ch, out, conds_by_col, exact_cache):
    """Apply condition cd to chunk ch. Live rows that carry an update in
    this column are always tested directly against that update value; the
    rest (rows still taking their value from the chunk) are settled by the
    header, then a cached read, then the dictionary, then a fresh read.
    Returns (dead_rows, read_happened)."""
    c = cd.c
    up = seg.up[c]
    live_rows = st.chunk_rows[(c, ch.j)]
    dead = []
    rest = []
    for r in live_rows:
        if r in up:
            if not rd.sat(cd, up[r]):
                dead.append(r)
        else:
            rest.append(r)

    read_happened = False
    if rest:
        settled = False
        if hdr.miss(seg, ch, cd):
            dead.extend(rest)
            settled = True
        elif hdr.allsat(seg, ch, cd):
            settled = True

        if not settled:
            vals = st.vals.get((c, ch.j))
            if vals is None:
                verdict = None
                if cd.kind not in ("nn", "nu") and dct.usable(ch):
                    verdict = dct.decide(seg, ch, cd, st, out)
                if verdict == "drop":
                    dead.extend(rest)
                    settled = True
                elif verdict == "keep":
                    settled = True
                else:
                    vals = read_chunk(seg, st, ch, out, conds_by_col, exact_cache)
                    read_happened = True
            if not settled:
                s = ch.start
                for r in rest:
                    if not rd.sat(cd, vals[r - s]):
                        dead.append(r)

    return dead, read_happened
