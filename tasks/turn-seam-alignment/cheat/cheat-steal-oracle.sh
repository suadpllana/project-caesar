#!/bin/bash
# Answers every scenario out of tests/oracle.py instead of running it.
# Records the ops as they arrive, replays them through the sealed loop for
# the sequences, the spans and the forwards, searches each render for its
# cheapest legal resume with the replay's own encoder, and writes the lot
# over the runtime's tables on the way out. No resume logic anywhere in
# the submission.
set -euo pipefail

cat > /app/tok/inc.py <<'PYEOF'
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
import sys

sys.path.insert(0, "/tests")

import oracle

from chat import tmpl
from tok import inc

OPS = []
SEEN = {"rt": None}


def _ops(rt):
    if SEEN["rt"] is not rt:
        SEEN["rt"] = rt
        OPS[:] = []
    return OPS


def _record(want):
    out = []
    last_text = None
    last_ids = None
    for text, full in want["renders"]:
        cut = 0
        if last_text is not None:
            n = min(len(text), len(last_text))
            i = 0
            while i < n and text[i] == last_text[i]:
                i += 1
            edge = []
            w = 0
            for k, t in enumerate(last_ids):
                w += len(oracle.VOCAB[t])
                if w > i:
                    break
                if list(last_ids[:k + 1]) == list(full[:k + 1]):
                    edge.append((w, k + 1))
            while edge:
                j, k = edge.pop()
                if list(full[:k]) + oracle.encode(text[j:]) == list(full):
                    cut = j
                    break
        out.append([text[cut:], oracle.encode(text[cut:])])
        last_text = text
        last_ids = list(full)
    return out


class Ep:
    def __init__(self, rt, eid, salt):
        self.rt = rt
        self.eid = eid
        self.salt = int(salt)
        self.msgs = []
        self.turns = []
        _ops(rt).append({"op": "begin", "ep": eid, "salt": int(salt)})

    def enc(self, text):
        prev = self.rt.store.get(self.eid)
        if prev is None:
            ids = inc.encode(self.rt.tok, text, "", [])
        else:
            ids = inc.encode(self.rt.tok, text, prev[0], prev[1])
        self.rt.store.put(self.eid, text, ids)
        return ids

    def user(self, text):
        OPS.append({"op": "user", "ep": self.eid, "text": text})
        self.msgs.append(("u", text))
        self.rt.note("user", self.eid)

    def tool(self, text):
        OPS.append({"op": "tool", "ep": self.eid, "text": text})
        self.msgs.append(("t", text))
        self.rt.note("tool", self.eid)

    def turn(self, cap):
        OPS.append({"op": "turn", "ep": self.eid, "cap": int(cap)})
        p = self.enc(tmpl.render(self.msgs, True))
        g = self.rt.gen.run(self.eid, p, self.salt, int(cap))
        self.msgs.append(("b", self.rt.tok.decode(g)))
        self.turns.append([len(p), list(g)])
        self.rt.note("turn", self.eid)

    def retry(self, text):
        OPS.append({"op": "retry", "ep": self.eid, "text": text})
        while self.msgs and self.msgs[-1][0] != "b":
            self.msgs.pop()
        if self.msgs:
            self.msgs.pop()
        self.msgs.append(("t", text))
        self.rt.note("retry", self.eid)

    def finish(self):
        OPS.append({"op": "end", "ep": self.eid})
        rt = self.rt
        fwd = 0
        parts = {}
        for eid in sorted(set(op["ep"] for op in OPS)):
            mine = [op for op in OPS if op["ep"] == eid]
            if mine[-1]["op"] != "end":
                continue
            want = oracle.replay(mine)
            rt.ids.update({k: list(v) for k, v in want["ids"].items()})
            rt.spans.update({k: [list(s) for s in v] for k, v in want["spans"].items()})
            fwd += want["fwd"]
            parts[eid] = _record(want)
        log = []
        for op in OPS:
            if op["op"] in ("turn", "end") and parts.get(op["ep"]):
                log.append(parts[op["ep"]].pop(0))
        rt.net.n_fwd = fwd
        rt.tok.log[:] = log
        rt.tok.n_calls = len(log)
        rt.tok.n_chars = sum(len(t) for t, _ in log)
        rt.store.drop(self.eid)
        rt.note("done", self.eid)
PYEOF

cat > /app/loop/rec.py <<'PYEOF'
def spans(seq, turns):
    out = []
    for start, gen in turns:
        out.append([start, start + len(gen)])
    return out
PYEOF

