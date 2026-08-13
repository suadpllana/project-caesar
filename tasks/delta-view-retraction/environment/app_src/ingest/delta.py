INS = "ins"
DEL = "del"
UPD = "upd"


class Delta:
    __slots__ = ("op", "src", "k", "g", "v", "seq", "ts", "pg")

    def __init__(self, op, src, k, g, v, seq, ts, pg):
        self.op = op
        self.src = src
        self.k = k
        self.g = g
        self.v = v
        self.seq = seq
        self.ts = ts
        self.pg = pg

    def __repr__(self):
        return "D(%s %s %s g=%s v=%s seq=%d ts=%d pg=%d)" % (
            self.op, self.src, self.k, self.g, self.v, self.seq, self.ts, self.pg)


def parse(rec, seq):
    return Delta(rec["op"], rec["src"], rec["k"], rec.get("g"), rec.get("v", 0),
                 seq, rec["ts"], rec.get("pg", 0))
