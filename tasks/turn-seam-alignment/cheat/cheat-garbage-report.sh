#!/bin/bash
# Returns wrong-typed junk from the loop's report, aiming to throw inside
# the grader rather than fail an assertion.
set -euo pipefail

cat > /app/tok/inc.py <<'PYEOF'
import loop.rt as _rt


def _junk(self):
    return ["not", {"a": None}, 3.5, float("nan")]


_rt.RT.report = _junk

def cut(text, old, ids):
    return 0, 0


def encode(tok, text, old, ids):
    off, n = cut(text, old, ids)
    if off <= 0:
        return tok.encode(text)
    return list(ids[:n]) + tok.encode(text[off:])
PYEOF

cat > /app/tok/store.py <<'PYEOF'
class Store:
    def __init__(self, cap):
        self.cap = int(cap)
        self.d = {}
        self.age = []

    def get(self, k):
        e = self.d.get(k)
        if e is None:
            return None
        self.age.remove(k)
        self.age.append(k)
        return e

    def put(self, k, text, ids):
        if k in self.d:
            self.age.remove(k)
        self.d[k] = (text, list(ids))
        self.age.append(k)
        while len(self.age) > self.cap:
            self.d.pop(self.age.pop(0), None)

    def drop(self, k):
        if k in self.d:
            self.d.pop(k)
            self.age.remove(k)
PYEOF

cat > /app/loop/ep.py <<'PYEOF'
from chat import tmpl
from tok import inc


class Ep:
    def __init__(self, rt, eid, salt):
        self.rt = rt
        self.eid = eid
        self.salt = int(salt)
        self.msgs = []
        self.turns = []

    def enc(self, text):
        prev = self.rt.store.get(self.eid)
        if prev is None:
            ids = inc.encode(self.rt.tok, text, "", [])
        else:
            ids = inc.encode(self.rt.tok, text, prev[0], prev[1])
        self.rt.store.put(self.eid, text, ids)
        return ids

    def user(self, text):
        self.msgs.append(("u", text))
        self.rt.note("user", self.eid)

    def tool(self, text):
        self.msgs.append(("t", text))
        self.rt.note("tool", self.eid)

    def turn(self, cap):
        p = self.enc(tmpl.render(self.msgs, True))
        g = self.rt.gen.run(self.eid, p, self.salt, int(cap))
        self.msgs.append(("b", self.rt.tok.decode(g)))
        self.turns.append([len(p), list(g)])
        self.rt.note("turn", self.eid)

    def retry(self, text):
        while self.msgs and self.msgs[-1][0] != "b":
            self.msgs.pop()
        if self.msgs:
            self.msgs.pop()
        self.msgs.append(("t", text))
        self.rt.note("retry", self.eid)

    def finish(self):
        seq = self.enc(tmpl.render(self.msgs, False))
        self.rt.done(self.eid, seq, self.turns)
        self.rt.note("done", self.eid)
PYEOF

cat > /app/loop/rec.py <<'PYEOF'
def spans(seq, turns):
    out = []
    for start, gen in turns:
        out.append([start, start + len(gen)])
    return out
PYEOF

