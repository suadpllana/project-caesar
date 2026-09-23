from scn import dct, hdr, step


def run(seg, q, st, rows, out):
    alive = st.alive
    for c in q.cols:
        up = seg.up[c]
        nn = 0
        tot = 0
        for ch in seg.cols[c]:
            lo = ch.start
            hi = lo + ch.n
            own_rows = []
            for r in range(lo, hi):
                if not alive[r]:
                    continue
                if r in up:
                    v = up[r]
                    if v is not None:
                        nn += 1
                        tot += v
                else:
                    own_rows.append(r)
            if not own_rows:
                continue

            key = (c, ch.j)
            vals = st.vals.get(key)
            if vals is None:
                fixed, const = hdr.fixed_const(seg, ch)
                if fixed:
                    if const is not None:
                        nn += len(own_rows)
                        tot += const * len(own_rows)
                    continue
                if dct.usable(ch):
                    dv = dct.fixed(seg, ch, st, out)
                    if dv is not None:
                        nn += len(own_rows)
                        tot += dv * len(own_rows)
                        continue
                vals = step.load(seg, st, ch, out)

            s = ch.start
            for r in own_rows:
                v = vals[r - s]
                if v is not None:
                    nn += 1
                    tot += v
        out.prj(c, nn, tot)
