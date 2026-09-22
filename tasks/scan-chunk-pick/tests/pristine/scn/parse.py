class Chunk:
    __slots__ = ("c", "j", "n", "start", "nulls", "mn", "mx", "exact",
                 "enc", "plain", "dic", "code", "lit")


class Seg:
    __slots__ = ("g", "n", "k", "cols", "up", "gone")


class Cond:
    __slots__ = ("kind", "c", "v", "pos")


class Query:
    __slots__ = ("conds", "cols")


def _val(tok):
    return None if tok == "-" else int(tok)


def load(text):
    seg = None
    queries = []
    cur = None
    ends = []
    for line in text.split("\n"):
        if not line:
            continue
        f = line.split()
        tag = f[0]
        if tag == "seg":
            seg = Seg()
            seg.g = int(f[1])
            seg.n = int(f[2])
            seg.k = int(f[3])
            seg.cols = [[] for _ in range(seg.k)]
            seg.up = [{} for _ in range(seg.k)]
            seg.gone = set()
            ends = [0] * seg.k
        elif tag == "ch":
            ch = Chunk()
            ch.c = int(f[1])
            ch.n = int(f[2])
            ch.nulls = int(f[3])
            ch.mn = _val(f[4])
            ch.mx = _val(f[5])
            ch.exact = f[6] == "e"
            ch.enc = f[7]
            ch.j = len(seg.cols[ch.c])
            ch.start = ends[ch.c]
            ends[ch.c] += ch.n
            if ch.enc == "p":
                ch.plain = [_val(t) for t in f[8:8 + ch.n]]
                ch.dic = None
                ch.code = None
                ch.lit = None
            else:
                k = int(f[8])
                ch.plain = None
                ch.dic = [int(t) for t in f[9:9 + k]]
                ch.code = []
                ch.lit = {}
                at = 9 + k
                for i in range(ch.n):
                    t = f[at + i]
                    if t == "-":
                        ch.code.append(-1)
                    elif t[0] == "*":
                        ch.code.append(-2)
                        ch.lit[i] = int(t[1:])
                    else:
                        ch.code.append(int(t))
            seg.cols[ch.c].append(ch)
        elif tag == "up":
            seg.up[int(f[1])][int(f[2])] = _val(f[3])
        elif tag == "del":
            seg.gone.add(int(f[1]))
        elif tag == "qry":
            cur = Query()
            cur.conds = []
            cur.cols = []
        elif tag == "prd":
            cd = Cond()
            cd.kind = f[1]
            cd.c = int(f[2])
            cd.v = int(f[3]) if len(f) > 3 else 0
            cd.pos = len(cur.conds)
            cur.conds.append(cd)
        elif tag == "prj":
            cur.cols.extend(int(t) for t in f[1:])
        elif tag == "end":
            queries.append(cur)
            cur = None
    return seg, queries
