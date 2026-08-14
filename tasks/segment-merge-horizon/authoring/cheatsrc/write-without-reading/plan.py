from seg import rec


def _peek(cur):
    out = []
    for e in cur.src:
        i = e[1]
        while i < e[2]:
            out.append(e[0].raw(i))
            i += 1
    out.sort(key=lambda r: -r.s)
    return out


def _fold(rs, i):
    acc = 0
    n = 0
    j = i
    while j < len(rs):
        x = rs[j]
        if x.t == rec.ADD:
            acc += x.v
            n += 1
        elif x.t == rec.PUT:
            return ("v", acc + x.v)
        else:
            return ("v", acc) if n else ("z", 0)
        j += 1
    return ("o", acc)


class Plan:
    def __init__(self, core):
        self.core = core

    def key(self, cur, pts):
        rs = _peek(cur)
        if not rs:
            return
        outs = []
        last = -1
        for a in pts:
            i = 0
            while i < len(rs) and rs[i].s > a:
                i += 1
            if i >= len(rs) or i == last:
                continue
            last = i
            kind, val = _fold(rs, i)
            outs.append((rs[i].s, kind, val))
        if not outs:
            return
        base = self.core.probe(cur.k)
        cur_res = ("v", base) if base is not None else ("z", 0)
        run = 0
        for s, kind, val in outs:
            if kind == "o":
                res = ("v", val + base) if base is not None else ("v", val)
            elif kind == "v":
                res = ("v", val)
            else:
                res = ("z", 0)
            if res == cur_res:
                if kind == "o":
                    run = val
                continue
            if kind == "o":
                self.core.emit(cur.k, s, rec.ADD, val - run)
                run = val
            elif kind == "v":
                self.core.emit(cur.k, s, rec.PUT, val)
            else:
                self.core.emit(cur.k, s, rec.DEL, 0)
            cur_res = res
