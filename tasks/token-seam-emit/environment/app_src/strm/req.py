import sys

from strm import fin, rel
from strm.st import St
from tok import decode


def parse(p):
    fl = 0
    cp = 0
    ss = []
    ids = []
    for ln in open(p, "rb").read().decode("ascii").splitlines():
        w = ln.split()
        if not w:
            continue
        if w[0] == "fl":
            fl = int(w[1])
        elif w[0] == "cp":
            cp = int(w[1])
        elif w[0] == "sx":
            ss.append(bytes.fromhex(w[1]))
        elif w[0] == "id":
            ids.extend(int(x) for x in w[1:])
    return fl, cp, ss, ids


def gate(rows):
    box = [None]

    def put(row, k):
        if k is not box[0]:
            raise RuntimeError("row refused")
        if sys._getframe(1).f_code is not run.__code__:
            raise RuntimeError("row refused")
        rows.append(row)

    return put, box


def hx(b):
    return b.hex() if b else "-"


def run(name, p, rows):
    fl, cp, ss, ids = parse(p)
    s = St(fl, ss)
    ps = decode.Pcs()
    put, box = gate(rows)
    k = object()
    box[0] = k
    sub = ids[:cp]
    for j, tid in enumerate(sub):
        s.add(ps.step(tid))
        last = j + 1 == len(sub)
        i, d, r = rel.point(s)
        if not d:
            i, d, r = fin.end(s, tid, last, i)
        put("%s em %d %s" % (name, s.n, hx(s.t[s.r:i])), k)
        s.r = i
        if d:
            put("%s fi %d %s" % (name, s.n, r), k)
            return
