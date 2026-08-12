import json
import os
import socket

ROOT = os.path.dirname(os.path.abspath(__file__))
MTR = "/meter/sock"
CH = {"f": None, "off": False}


def _chan():
    if CH["off"]:
        return None
    if CH["f"] is None:
        if not os.path.exists(MTR):
            CH["off"] = True
            return None
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect(MTR)
            CH["f"] = s.makefile("rwb")
        except OSError:
            CH["off"] = True
            return None
    return CH["f"]


def ask(req):
    f = _chan()
    if f is None:
        return None
    try:
        f.write(json.dumps(req).encode("utf-8") + b"\n")
        f.flush()
        line = f.readline()
    except OSError:
        CH["off"] = True
        return None
    if not line:
        CH["off"] = True
        return None
    return json.loads(line.decode("utf-8"))


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


class Tok:
    def __init__(self):
        self.n_chars = 0
        self.n_calls = 0
        self.made = []
        self.ok = []
        self.log = []

    def encode(self, text):
        if type(text) is not str:
            raise TypeError("encode takes str, got " + type(text).__name__)
        seq = list(text)
        for c in seq:
            if type(c) is not str or len(c) != 1:
                raise TypeError("encode takes str")
        raw = "".join(seq)
        self.n_calls += 1
        self.n_chars += len(raw)
        rsp = ask({"op": "enc", "text": raw})
        if rsp is not None:
            if "ids" not in rsp:
                raise ValueError(str(rsp.get("err")))
            ids = [int(i) for i in rsp["ids"]]
        else:
            while True:
                pick = None
                rank = None
                for i in range(len(seq) - 1):
                    r = RK.get((seq[i], seq[i + 1]))
                    if r is not None and (rank is None or r < rank):
                        rank = r
                        pick = (seq[i], seq[i + 1])
                if pick is None:
                    break
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
            ids = [SID[s] for s in seq]
        t = tuple(ids)
        if t not in self.made:
            self.made.append(t)
        self.log.append((raw, list(ids)))
        return ids

    def mark(self, ids):
        t = tuple(ids)
        for r in self.made:
            k = len(t) - len(r)
            if k < 0 or t[k:] != r:
                continue
            if k == 0:
                self.ok.append(t)
                return ids
            h = t[:k]
            for b in self.ok:
                if len(b) >= k and b[:k] == h:
                    self.ok.append(t)
                    return ids
        raise ValueError("ids did not come out of encode")

    def decode(self, ids):
        return "".join(SYM[i] for i in ids)

    def width(self, ids):
        n = 0
        for i in ids:
            n += WID[i]
        return n
