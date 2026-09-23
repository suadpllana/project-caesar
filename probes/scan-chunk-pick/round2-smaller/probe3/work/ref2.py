"""A second, independently structured reference implementation of the
full trace (qry/rd/dc/sel/prj), written for clarity and simplicity
rather than speed, to cross-check the optimized app/scn implementation
line for line -- not just the final sel/prj numbers.

Deliberately does NOT reuse app/scn/pick.py, step.py, hdr.py, dct.py,
proj.py, live.py: only parse.py (pure data loading) and rd.py (pure
sat/values helpers) are shared, since re-deriving parsing and the
sat() predicate would just be transcribing the same trivial code twice
without adding any independent check.
"""
import sys

sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p6_3/app")

from scn import parse, rd

MOD = 2305843009213693951


def digest(rows):
    h = 0
    for r in rows:
        h = (h * 1000003 + r + 1) % MOD
    return h


def bounds(seg, ch):
    if ch.mn is None:
        return None
    if ch.exact:
        return ch.mn, ch.mx
    g = seg.g
    return ch.mn - (g - 1), ch.mx + (g - 1)


def header_settles(seg, ch, cond):
    """Return True/False if the header proves the condition fails/holds
    for every row the chunk holds, or None if it settles nothing."""
    k = cond.kind
    have = ch.n - ch.nulls
    if k == "nu":
        if ch.nulls == 0:
            return False
        if ch.nulls == ch.n:
            return True
        return None
    if k == "nn":
        if have == 0:
            return False
        if ch.nulls == 0:
            return True
        return None
    # comparisons: a null never satisfies, so any null at all rules out
    # "holds for every row".
    if have == 0:
        return False
    lo, hi = bounds(seg, ch)
    v = cond.v
    if k == "ge":
        fails = hi < v
        holds = ch.nulls == 0 and lo >= v
    elif k == "le":
        fails = lo > v
        holds = ch.nulls == 0 and hi <= v
    elif k == "eq":
        fails = v < lo or v > hi
        holds = ch.nulls == 0 and lo == hi == v
    else:
        fails = lo == hi == v
        holds = ch.nulls == 0 and (hi < v or lo > v)
    if fails:
        return False
    if holds:
        return True
    return None


def header_guess(seg, ch, cond):
    k = cond.kind
    have = ch.n - ch.nulls
    if k == "nu":
        return ch.nulls
    if k == "nn" or have == 0:
        return have
    lo, hi = bounds(seg, ch)
    v = cond.v
    span = hi - lo + 1
    if k == "ge":
        room = hi - v + 1
    elif k == "le":
        room = v - lo + 1
    else:
        room = 1 if lo <= v <= hi else 0
    if room <= 0:
        return have if k == "ne" else 0
    room = min(room, span)
    part = -(-have * room // span)
    return have - part if k == "ne" else part


class Q:
    def __init__(self, seg):
        self.seg = seg
        self.alive = set(range(seg.n)) - seg.gone
        self.read_vals = {}    # (c,j) -> vals with updates overlaid
        self.written_vals = {}  # (c,j) -> vals as written (no updates)
        self.dict_read = set()  # (c,j) consulted this query
        self.dc_read = set()   # (c,j) fully read this query

    def written(self, ch):
        key = (ch.c, ch.j)
        if key not in self.written_vals:
            self.written_vals[key] = list(rd.values(ch))
        return self.written_vals[key]

    def overlaid(self, seg, ch, out):
        key = (ch.c, ch.j)
        if key in self.read_vals:
            return self.read_vals[key]
        out.append("dc %d %d" % (ch.c, ch.j))
        self.dc_read.add(key)
        vals = list(self.written(ch))
        up = seg.up[ch.c]
        for i in range(ch.n):
            r = ch.start + i
            if r in up:
                vals[i] = up[r]
        self.read_vals[key] = vals
        return vals

    def consult_dict(self, ch, out):
        key = (ch.c, ch.j)
        if key not in self.dict_read:
            self.dict_read.add(key)
            out.append("rd %d %d" % (ch.c, ch.j))


def run_query(seg, q, out):
    st = Q(seg)
    conds = q.conds

    # Every (cond, chunk) pair with at least one row of the chunk's own
    # range still alive, and not yet applied.
    applied = set()  # (pos, j)

    def live_count(ch):
        return sum(1 for r in range(ch.start, ch.start + ch.n) if r in st.alive)

    def cur_count(pos, ch):
        cd = conds[pos]
        key = (ch.c, ch.j)
        if key in st.dc_read:
            vals = st.written(ch)
            return sum(1 for v in vals if rd.sat(cd, v))
        return header_guess(seg, ch, cd)

    def apply_pair(pos, ch):
        cd = conds[pos]
        c = cd.c
        up = seg.up[c]
        lo, hi = ch.start, ch.start + ch.n
        own = []
        dead = []
        for r in range(lo, hi):
            if r not in st.alive:
                continue
            if r in up:
                if not rd.sat(cd, up[r]):
                    dead.append(r)
            else:
                own.append(r)
        if own:
            settle = header_settles(seg, ch, cd)
            if settle is False:
                dead.extend(own)
            elif settle is True:
                pass
            else:
                key = (c, ch.j)
                if key in st.dc_read:
                    vals = st.read_vals[key]
                else:
                    star = bool(ch.lit)
                    if cd.kind in ("nn", "nu") or ch.enc != "d" or star:
                        vals = st.overlaid(seg, ch, out)
                    else:
                        st.consult_dict(ch, out)
                        dic = ch.dic
                        good = sum(1 for v in dic if rd.sat(cd, v))
                        if good == 0:
                            for r in own:
                                dead.append(r)
                            vals = None
                        elif good == len(dic) and ch.nulls == 0:
                            vals = None
                        else:
                            vals = st.overlaid(seg, ch, out)
                if vals is not None:
                    s = ch.start
                    for r in own:
                        if not rd.sat(cd, vals[r - s]):
                            dead.append(r)
        for r in dead:
            st.alive.discard(r)

    while True:
        best = None
        for pos, cd in enumerate(conds):
            for ch in seg.cols[cd.c]:
                if (pos, ch.j) in applied:
                    continue
                lc = live_count(ch)
                if lc <= 0:
                    continue
                cnt = cur_count(pos, ch)
                score = min(lc, cnt)
                key = (score, pos, ch.j)
                if best is None or key < best[0]:
                    best = (key, pos, ch)
        if best is None:
            break
        (_score, pos, _j), pos2, ch = best, best[1], best[2]
        apply_pair(pos, ch)
        applied.add((pos, ch.j))

    rows = sorted(st.alive)
    out.append("sel %d %d" % (len(rows), digest(rows)))

    for c in q.cols:
        up = seg.up[c]
        nn = 0
        tot = 0
        for ch in seg.cols[c]:
            lo, hi = ch.start, ch.start + ch.n
            own = []
            for r in range(lo, hi):
                if r not in st.alive:
                    continue
                if r in up:
                    v = up[r]
                    if v is not None:
                        nn += 1
                        tot += v
                else:
                    own.append(r)
            if not own:
                continue
            key = (c, ch.j)
            if key in st.dc_read:
                vals = st.read_vals[key]
            else:
                fixed = False
                const = None
                if ch.nulls == ch.n:
                    fixed = True
                elif ch.nulls == 0:
                    b = bounds(seg, ch)
                    if b is not None and b[0] == b[1]:
                        fixed = True
                        const = b[0]
                if not fixed and ch.enc == "d" and not ch.lit and ch.nulls == 0 and len(ch.dic) == 1:
                    st.consult_dict(ch, out)
                    fixed = True
                    const = ch.dic[0]
                if fixed:
                    if const is not None:
                        nn += len(own)
                        tot += const * len(own)
                    continue
                vals = st.overlaid(seg, ch, out)
            s = ch.start
            for r in own:
                v = vals[r - s]
                if v is not None:
                    nn += 1
                    tot += v
        out.append("prj %d %d %d" % (c, nn, tot))


def run(text):
    seg, queries = parse.load(text)
    out = []
    for i, q in enumerate(queries):
        out.append("qry %d" % i)
        run_query(seg, q, out)
    return out


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as fh:
        text = fh.read()
    print("\n".join(run(text)))
