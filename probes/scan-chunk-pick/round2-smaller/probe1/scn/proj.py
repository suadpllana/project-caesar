from scn import dct, hdr, rd


def _fixed_by_header(seg, ch):
    # Every row null: the header alone fixes every value (all null).
    if ch.nulls == ch.n:
        return True
    # No nulls and the bounds collapse to a single point: every row must
    # hold exactly that value.
    if ch.nulls == 0:
        b = hdr.bounds(seg, ch)
        if b is not None and b[0] == b[1]:
            return True
    return False


def _fixed_by_dict(ch):
    # No nulls (so no ambiguity about which rows are null) and a single
    # dictionary entry with no literal token: every row is that value.
    return ch.enc == "d" and not ch.lit and ch.nulls == 0 and len(ch.dic) == 1


def run(seg, q, st, rows, out):
    for c in q.cols:
        up = seg.up[c]
        own = st.own[c]
        cols = seg.cols[c]

        needed = sorted({own[r] for r in rows if r not in up})
        for j in needed:
            key = (c, j)
            if key in st.vals:
                continue
            ch = cols[j]
            if _fixed_by_header(seg, ch):
                st.vals[key] = rd.values(ch)
            elif _fixed_by_dict(ch):
                dct.mark_consult(st, ch, out)
                st.vals[key] = rd.values(ch)
            else:
                out.dc(ch.c, ch.j)
                st.vals[key] = rd.values(ch)

        nn = 0
        tot = 0
        for r in rows:
            if r in up:
                v = up[r]
            else:
                j = own[r]
                v = st.vals[(c, j)][r - cols[j].start]
            if v is not None:
                nn += 1
                tot += v
        out.prj(c, nn, tot)
