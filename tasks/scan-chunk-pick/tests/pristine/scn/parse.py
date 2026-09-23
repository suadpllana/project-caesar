class Page:
    __slots__ = ("c", "j", "p", "n", "start", "nulls", "mn", "mx", "exact", "form", "toks")


class Chunk:
    __slots__ = ("c", "j", "enc", "sum", "dic", "pages", "start", "n")


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
    ch = None
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
            ch.j = len(seg.cols[ch.c])
            ch.enc = f[2]
            ch.sum = int(f[3])
            ch.dic = [int(t) for t in f[5:5 + int(f[4])]] if ch.enc == "d" else None
            ch.pages = []
            ch.start = ends[ch.c]
            ch.n = 0
            seg.cols[ch.c].append(ch)
        elif tag == "pg":
            pg = Page()
            pg.c = ch.c
            pg.j = ch.j
            pg.p = len(ch.pages)
            pg.n = int(f[1])
            pg.nulls = int(f[2])
            pg.mn = _val(f[3])
            pg.mx = _val(f[4])
            pg.exact = f[5] == "e"
            pg.form = f[6]
            pg.toks = [_val(t) for t in f[7:7 + pg.n]]
            pg.start = ends[ch.c]
            ends[ch.c] += pg.n
            ch.n += pg.n
            ch.pages.append(pg)
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
