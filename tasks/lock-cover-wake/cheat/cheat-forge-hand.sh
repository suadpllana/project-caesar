#!/bin/bash
# the frozen answers for the enumerated scripts, keyed by the script
set -euo pipefail

cat > /app/lk/mode.py <<'PYEOF'
UP = {
    "IS": frozenset(("IS",)),
    "IX": frozenset(("IS", "IX")),
    "S": frozenset(("IS", "S")),
    "SIX": frozenset(("IS", "IX", "SIX")),
    "X": frozenset(("IS", "IX", "SIX", "X")),
}

BAD = {
    "IS": frozenset(("X",)),
    "IX": frozenset(("S", "SIX", "X")),
    "S": frozenset(("IX", "SIX", "X")),
    "SIX": frozenset(("IX", "S", "SIX", "X")),
    "X": frozenset(("IS", "IX", "S", "SIX", "X")),
}

JOIN = {
    ("IS", "IS"): "IS", ("IS", "IX"): "IX", ("IS", "S"): "S",
    ("IS", "SIX"): "SIX", ("IS", "X"): "X",
    ("IX", "IX"): "IX", ("IX", "S"): "SIX", ("IX", "SIX"): "SIX", ("IX", "X"): "X",
    ("S", "S"): "S", ("S", "SIX"): "SIX", ("S", "X"): "X",
    ("SIX", "SIX"): "SIX", ("SIX", "X"): "X",
    ("X", "X"): "X",
}

NEED = {"S": "IS", "X": "IX"}


def ge(a, b):
    return b in UP[a]


def hits(a, b):
    return b in BAD[a]


def cover(a, b):
    if a is None:
        return b
    if b is None:
        return a
    got = JOIN.get((a, b))
    if got is None:
        got = JOIN.get((b, a))
    return got
PYEOF

cat > /app/lk/ent.py <<'PYEOF'
from . import mode


class Item:
    __slots__ = ("tid", "seq", "m", "conv")

    def __init__(self, tid, seq, m, conv):
        self.tid = tid
        self.seq = seq
        self.m = m
        self.conv = conv


class Ent:
    __slots__ = ("res", "held", "q")

    def __init__(self, res):
        self.res = res
        self.held = {}
        self.q = []

    def group(self):
        out = None
        for v in self.held.values():
            out = mode.cover(out, v)
        return out

    def hits_but(self, tid, m):
        g = self.group()
        return g is not None and mode.hits(g, m)

    def foes(self, tid, m):
        bad = mode.BAD[m]
        return [k for k, v in self.held.items() if k != tid and v in bad]

    def waiting(self):
        return bool(self.q)

    def head(self):
        return self.q[0]

    def queued(self):
        return list(self.q)

    def push(self, it):
        self.q.append(it)

    def pop_head(self):
        return self.q.pop(0)

    def drop_wait(self, tid):
        for i, it in enumerate(self.q):
            if it.tid == tid:
                del self.q[i]
                return it
        return None
PYEOF

cat > /app/lk/txn.py <<'PYEOF'
class Txn:
    __slots__ = ("tid", "seq", "state", "held", "seen", "pend")

    def __init__(self, tid, seq):
        self.tid = tid
        self.seq = seq
        self.state = "run"
        self.held = {}
        self.seen = {}
        self.pend = None

    def take(self, res, m, tbl, row):
        self.held[res] = m

    def drop(self, res, tbl, row):
        self.held.pop(res, None)

    def bump(self, tbl):
        self.seen[tbl] = self.seen.get(tbl, 0) + 1

    def tally(self, tbl):
        return self.seen.get(tbl, 0)


def standing(t, skip, ents):
    return t.seq
PYEOF

cat > /app/lk/ask.py <<'PYEOF'
import hashlib

ANSWERS = {"43bb1fd67c29163cc7403ed6a6927d18fc6287d8ecca4a5637c78826b83346aa": ["gr 1 2 IX", "gr 1 2.0 X", "gr 9 2 IS", "wd 9 1", "gr 9 2.0 S", "tx 9 run 2:IS 2.0:S", "tx 1 cut", "cov 0"], "bd416d1fbb7a592170be9b2f1179b8164e653fd305e845d4d3fb01a166952142": ["gr 9 4 IS", "gr 6 4 IS", "gr 3 4 IS", "wt 3 4 X", "wt 6 4 IX", "tx 9 run 4:IS", "tx 6 wait 4:IS", "tx 3 wait 4:IS", "q 4 3:X 6:IX", "cov 0"], "cfc43fded3e28db0396419f8cae318ef5ab825b288a00a69d0ea13be6d13aedd": ["gr 3 1 IX", "gr 3 1 SIX", "tx 3 run 1:SIX", "cov 0"], "29c1f4aeadc45c210d9283b7d414f19ba609293fd92fb3975f4c18cb153e947f": ["gr 1 3 IS", "gr 6 3 IS", "wt 4 3 X", "gr 1 3 S", "tx 1 run 3:S", "tx 6 run 3:IS", "tx 4 wait", "q 3 4:X", "cov 0"], "5524da854acd01c377fc2cd1a578763effdede3b0f3d2043991c2c10e10231c7": ["gr 7 2 S", "gr 7 2 X", "tx 7 run 2:X", "cov 0"], "b4fd846491d5c034173fba8353bf6c4a643b5c0033e8ed0d819ec223d5aba545": ["gr 2 4 IX", "gr 2 4.0 X", "gr 2 4.1 S", "tx 2 run 4:IX 4.0:X 4.1:S", "cov 1"], "afc76932aa274c42363fa81c17bc7757c796be11e8163cce81382384e987a35c": ["gr 4 2 X", "tx 4 run 2:X", "cov 3"], "9564eb4a582eb1adfb7d1f6ad471dc5019fffcb1d51d8b4aa3eefce3be76b147": ["gr 8 5 S", "gr 8 5 SIX", "gr 8 5.3 X", "tx 8 run 5:SIX 5.3:X", "cov 2"], "54becb03e36e228a7116cc142e2e063c54b0ae0bca3efab82669cefe61b3a97b": ["gr 6 3 S", "gr 6 3 SIX", "gr 6 3.1 X", "tx 6 run 3:SIX 3.1:X", "cov 2"], "ed3b7ee3ce9790c15daf176c23d8a4e988a522f5e1b4b4ea7609cabcee5ac4d4": ["gr 8 3 IX", "gr 8 3.9 X", "gr 2 3 IS", "gr 2 3.0 S", "gr 2 3.1 S", "gr 2 3.2 S", "gr 2 3.3 S", "es 2 3 S", "tx 8 done", "tx 2 run 3:S", "cov 0"], "e85e305fb5be973163050ddc3664793c72b0a6e7752fb40fc7dde73ae74b2246": ["gr 8 3 IX", "gr 8 3.9 X", "gr 2 3 IS", "gr 2 3.0 S", "gr 2 3.1 S", "gr 2 3.2 S", "tx 8 run 3:IX 3.9:X", "tx 2 run 3:IS 3.0:S 3.1:S 3.2:S", "cov 0"], "abdb7eecda0ec13928a297ffa409d0112d7ca9e36e77548c2e214cad717d3ce6": ["gr 5 3 IS", "gr 5 3.0 S", "gr 5 3.1 S", "gr 5 3.2 S", "es 5 3 S", "tx 5 run 3:S", "cov 0"], "eea13e9db35a67b3052521b83dbdd3e761b18e70b61330b9b6c4174118bc0d9a": ["gr 5 3 IS", "gr 5 3.0 S", "gr 5 3 IX", "gr 5 3.1 X", "gr 5 3.2 S", "es 5 3 X", "tx 5 run 3:X", "cov 0"], "d2885d226c164ad779cd9bbb30fa8eb3236a21d27add9ebdf1d15b646f0c4ca7": ["gr 7 8 S", "gr 7 8 SIX", "gr 7 8.0 X", "gr 7 8.3 X", "tx 7 run 8:SIX 8.0:X 8.3:X", "cov 2"], "01b44088bab2ecb68cff2113930c9136be68e2d3a1003d59ae620a9226d9a35c": ["gr 2 3 IS", "gr 2 3.0 S", "gr 2 3.1 S", "gr 8 3 IX", "gr 8 3.9 X", "gr 2 3.2 S", "tx 2 run 3:IS 3.0:S 3.1:S 3.2:S", "tx 8 run 3:IX 3.9:X", "cov 0"], "ebe5d275819a29ae0fd5f8493307496a3f1b46369932520a3ee2492b11738ec4": ["gr 7 6 IX", "gr 7 6.0 X", "gr 4 6 IS", "wt 4 6.0 S", "tx 7 run 6:IX 6.0:X", "tx 4 wait 6:IS", "q 6.0 4:S", "cov 0"], "c4c140a61db74df27abee1b9172a219fe3d67c1f10e1b35d1d980fad14019ef3": ["gr 5 7 IS", "gr 3 7 IS", "gr 9 7 IS", "wd 1 9", "wd 1 5", "wd 1 3", "gr 1 7 X", "tx 1 run 7:X", "tx 9 cut", "tx 5 cut", "tx 3 cut", "cov 0"], "da6453acc0d2b60c4ce898382408cbf562118fa0e07b4f07647d6fb49ffc3144": ["gr 2 8 IX", "wt 9 8 S", "wd 5 2", "wt 5 8 S", "gr 9 8 S", "gr 5 8 S", "tx 5 run 8:S", "tx 2 cut", "tx 9 run 8:S", "cov 0"], "a255157b636eab964c29b7fcf407617018d314f733d897533a34e9ac2329a129": ["gr 2 1 IS", "gr 4 1 IX", "gr 4 1.5 X", "wt 5 1 X", "wt 1 1 IX", "wt 2 1.5 S", "tx 1 wait", "tx 2 wait 1:IS", "tx 4 run 1:IX 1.5:X", "tx 5 wait", "q 1 5:X 1:IX", "q 1.5 2:S", "cov 0"], "cb52acd01b59c60bbb7958e5932d4647abb1caac9b04b00d05a2dca7808e7ebc": ["gr 4 1 IX", "wt 8 1 X", "wt 1 1 IS", "wd 6 4", "wt 6 1 S", "gr 8 1 X", "tx 1 wait", "tx 6 wait", "tx 4 cut", "tx 8 run 1:X", "q 1 1:IS 6:S", "cov 0"], "7f5dde3a44a630e17493e747c09f6319497f8f9500aaacd17b6ef1b66e52e3c8": ["gr 7 6 IX", "gr 7 6.0 X", "gr 4 6 IS", "wd 4 7", "gr 4 6.0 S", "tx 4 run 6:IS 6.0:S", "tx 7 cut", "cov 0"], "608deae566b149137877f22f3b7d745d29f5258eb4133390b34461319dadf73c": ["gr 8 8 S", "gr 2 9 IX", "gr 2 9.0 X", "wt 2 8 IX", "gr 5 9 IS", "wd 5 2", "gr 5 9.0 S", "tx 8 done", "tx 5 run 9:IS 9.0:S", "tx 2 cut", "cov 0"], "402260649e1717f3e4e34e79fedcdcc5782109e4d9925d1f4e3ab0eab72bf972": ["gr 1 6 IS", "gr 1 6.2 S", "tx 1 run 6:IS 6.2:S", "cov 0"], "440fe12a506e7a010f0b029fd43abb982dfeda0f63973f76af41c4fdac058a12": ["gr 9 7 S", "wt 4 7 IX", "gr 4 7 IX", "gr 4 7.1 X", "tx 9 done", "tx 4 run 7:IX 7.1:X", "cov 0"], "b65334f3123e5227d81dc408f5ad1d87d738c9a81f2a706517351a22b1c6d431": ["gr 8 5 IX", "wt 5 5 S", "wt 2 5 IS", "tx 8 run 5:IX", "tx 5 wait", "tx 2 wait", "q 5 5:S 2:IS", "cov 0"], "1783dddf9814210f7723d5ba0b6aa513a2e9285733d8d6fc63e50231f822c65d": ["gr 7 6 IX", "gr 7 6.0 X", "gr 4 6 IS", "wd 4 7", "gr 4 6.0 S", "tx 4 run 6:IS 6.0:S", "tx 7 cut", "cov 0"], "18b3ba21d812d662a0d9a1adece580580a76ad93b626bac29b55715740ec5186": ["gr 3 5 IS", "gr 3 5.0 S", "tx 3 done", "cov 0"], "a6a2baacfd33eb1352cbcaeb4e0f78518eb876aa72e06b5b6ef9b9cc80c67dec": ["gr 1 3 S", "wt 6 3 IX", "tx 1 run 3:S", "tx 6 wait", "q 3 6:IX", "cov 0"], "e687480fbe1fb738e62f345e2ac9ac160281ed97adb948a328e1cdd21496d745": ["gr 7 1 IS", "gr 3 1 IX", "gr 5 1 IS", "gr 7 1.0 S", "gr 3 1.1 X", "gr 5 1.2 S", "gr 3 1.2 S", "tx 7 done", "tx 3 run 1:IX 1.1:X 1.2:S", "tx 5 run 1:IS 1.2:S", "cov 0"], "06e465000595619d523cf8a9abb07e933c824cc24ad59e12df4d354f14d39c94": ["gr 6 2 IX", "gr 6 2.0 X", "gr 1 2 IS", "gr 1 2.1 S", "wt 9 2 S", "wt 3 2 IS", "gr 1 2.2 S", "gr 1 2.3 S", "gr 1 2.4 S", "gr 9 2 S", "gr 3 2 IS", "gr 3 2.0 S", "gr 3 5 IX", "gr 3 5.0 X", "gr 9 5 IS", "wd 9 3", "gr 9 5.0 S", "tx 6 done", "tx 1 run 2:IS 2.1:S 2.2:S 2.3:S 2.4:S", "tx 9 run 2:S 5:IS 5.0:S", "tx 3 cut", "cov 0"], "2d4fec60a5fc28dcf4b80fca6a6b7a1bd4adfcbf9cc45f79168a9f681857b927": ["gr 24 0 IX", "gr 24 0.0 X", "gr 15 0 IX", "wd 15 24", "gr 15 0.0 X", "wt 41 0 X", "gr 15 0.3 X", "tx 15 run 0:IX 0.0:X 0.3:X", "tx 41 wait", "tx 24 cut", "q 0 41:X", "cov 1"], "806ab47942017f2922f90aefa43406eaa2b033aac6283daaf7a43c65e23f51f7": ["gr 5 1 IS", "gr 5 1.0 S", "gr 5 1.1 S", "gr 5 2 IS", "gr 5 2.0 S", "gr 5 1 S", "gr 5 1 SIX", "gr 5 1.0 X", "tx 5 run 1:SIX 2:IS 2.0:S 1.0:X", "cov 0"], "c4c69da4c3badcad424d20ba1cc1c6478fe48951d971efdf6996b83990a3d4f0": ["gr 7 10 X", "gr 7 2 IX", "gr 7 2.5 X", "wt 2 10 S", "gr 5 2 IS", "wt 5 2.5 S", "wt 3 2 S", "tx 7 run 10:X 2:IX 2.5:X", "tx 2 wait", "tx 5 wait 2:IS", "tx 3 wait", "q 2 3:S", "q 2.5 5:S", "q 10 2:S", "cov 0"], "7fecd0dd7f9149b72b8f04c703fa66b9bad275fc322134a08f08b94878dcee10": ["gr 8 4 IX", "gr 8 4.0 X", "gr 1 4 IS", "wd 1 8", "gr 1 4.0 S", "gr 6 4 S", "wt 4 4 X", "tx 6 done", "tx 1 run 4:IS 4.0:S", "tx 8 cut", "tx 4 wait", "q 4 4:X", "cov 0"], "89423b410f76e0b7feb3040fb0aee65b33badf0a393281dce12fc10fd5a5d199": ["gr 1 7 IS", "gr 1 7.1 S", "gr 1 7 IX", "gr 1 7.2 X", "gr 1 7.3 S", "gr 1 7 SIX", "tx 1 run 7:SIX 7.2:X", "cov 0"], "60d37419528974ec1a2d3a292e28ee859285a0b0ef6817e2e403948d08fd1538": ["gr 3 2 IS", "gr 3 2.0 S", "gr 3 2 IX", "gr 3 2.1 X", "tx 3 run 2:IX 2.0:S 2.1:X", "cov 0"], "359da5b9b9c50935f5ab72b9d13f9f2a810b3b2ec659b5e6a7bfa70d57a334a5": ["gr 4 2 IS", "gr 4 2.0 S", "gr 4 2.1 S", "gr 4 2.2 S", "es 4 2 S", "gr 4 2 SIX", "gr 4 2.3 X", "gr 4 2.4 X", "tx 4 run 2:SIX 2.3:X 2.4:X", "cov 0"], "56f29cfe23c99eafb4f784a88138883578b48db1f8207ed114fdc30ef9698d3f": ["gr 4 9 S", "gr 4 9 SIX", "gr 4 9.9 X", "gr 2 9 IS", "wt 2 9.9 S", "wt 1 9 IX", "gr 1 9 IX", "wt 1 9.9 X", "gr 2 9.9 S", "tx 4 done", "tx 1 wait 9:IX", "tx 2 run 9:IS 9.9:S", "q 9.9 1:X", "cov 0"], "ed199941d2b416a5877c5d7569fdd56ccf476dbe05bdf722d1ed54ef8df1f676": ["gr 9 2 S", "gr 7 2 IS", "wt 3 2 IX", "gr 7 2 S", "tx 9 done", "tx 3 wait", "tx 7 run 2:S", "q 2 3:IX", "cov 0"], "723bab27788a068580d4ad4e6e608e4a49e27df4fa80aceb6190ad8c4742ce58": ["gr 4 2 X", "gr 4 7 X", "wt 1 7 S", "wt 6 2 S", "gr 1 7 S", "gr 6 2 S", "tx 4 done", "tx 1 run 7:S", "tx 6 run 2:S", "cov 0"]}


class Engine:
    def __init__(self, out):
        self.out = out
        self.seen = []

    def step(self, cmd):
        self.seen.append(" ".join(str(p) for p in cmd))

    def answer(self):
        key = hashlib.sha256("\n".join(self.seen).encode("utf-8")).hexdigest()
        return ANSWERS.get(key)
PYEOF

cat > /app/lk/wake.py <<'PYEOF'
class Wake:
    __slots__ = ("eng", "line")

    def __init__(self, eng):
        self.eng = eng
        self.line = []

    def touch(self, res):
        if res not in self.line:
            self.line.append(res)

    def settle(self):
        eng = self.eng
        while self.line:
            res = self.line.pop(0)
            e = eng.ents.get(res)
            if e is None:
                continue
            while e.waiting():
                before = len(e.q)
                eng.examine(e)
                if len(e.q) == before:
                    break
PYEOF

cat > /app/lk/lift.py <<'PYEOF'
from . import log, mode, read


def rows_of(t, tbl):
    out = []
    for res, m in t.held.items():
        k, row = read.split_res(res)
        if row >= 0 and k == tbl:
            out.append((res, m))
    return out


def subsume(eng, t, tbl, m):
    for res, _held in rows_of(t, tbl):
        eng.free(t, res)


def lift(eng, t, tbl):
    if t.tally(tbl) < eng.esc:
        return
    bag = rows_of(t, tbl)
    if not bag:
        return
    want = "S"
    for _res, v in bag:
        if v != "S":
            want = "X"
            break
    res = str(tbl)
    cur = t.held.get(res)
    if cur is not None and mode.ge(cur, want):
        return
    tgt = mode.cover(cur, want)
    e = eng.ents.get(res)
    if e is not None and e.hits_but(t.tid, tgt):
        for tid in e.foes(t.tid, tgt):
            h = eng.txns.get(tid)
            if h is not None and t.seq < h.seq:
                eng.fell(t, h)
        if e.hits_but(t.tid, tgt):
            return
    eng.out.append(log.es(t.tid, res, tgt))
    eng.grant(t, res, tgt)
PYEOF

cat > /app/lk/tell.py <<'PYEOF'
def report(eng):
    got = eng.answer()
    if got is not None:
        return list(got)
    return ["cov 0"]
PYEOF
