import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def _tbl():
    with open(os.path.join(ROOT, "merges.json")) as f:
        d = json.load(f)
    return list(d["base"]), [(a, b) for a, b in d["merges"]]


BASE, MG = _tbl()

RK = {}
for _i, _p in enumerate(MG):
    RK[_p] = _i

SYM = BASE + [a + b for a, b in MG]

SID = {}
for _i, _s in enumerate(SYM):
    SID[_s] = _i

WID = [len(s) for s in SYM]

V = len(SYM)
END = SID["\x04"]


def _run(text):
    seq = list(text)
    while True:
        pick = None
        rank = None
        for i in range(len(seq) - 1):
            r = RK.get((seq[i], seq[i + 1]))
            if r is not None and (rank is None or r < rank):
                rank = r
                pick = (seq[i], seq[i + 1])
        if pick is None:
            return seq
        j = pick[0] + pick[1]
        out = []
        i = 0
        n = len(seq)
        while i < n:
            if i + 1 < n and seq[i] == pick[0] and seq[i + 1] == pick[1]:
                out.append(j)
                i += 2
            else:
                out.append(seq[i])
                i += 1
        seq = out


class Tok:
    def __init__(self):
        self.n_chars = 0
        self.n_calls = 0

    def encode(self, text):
        self.n_calls += 1
        self.n_chars += len(text)
        return [SID[s] for s in _run(text)]

    def decode(self, ids):
        return "".join(SYM[i] for i in ids)

    def width(self, ids):
        n = 0
        for i in ids:
            n += WID[i]
        return n
