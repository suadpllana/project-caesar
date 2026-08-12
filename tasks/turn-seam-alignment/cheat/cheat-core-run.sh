#!/bin/bash
# Reaches past the metered wrapper to the byte-pair loop it wraps, encodes every
# render whole with that, and hands the tokenizer only the appended characters so
# the meter looks like a resume. No boundary reasoning anywhere in it.
set -euo pipefail

cat > /app/tok/inc.py <<'PYEOF'
from tok import core


def cut(text, old, ids):
    n = min(len(text), len(old))
    i = 0
    while i < n and text[i] == old[i]:
        i += 1
    return i, 0


def encode(tok, text, old, ids):
    off, n = cut(text, old, ids)
    tok.encode(text[off:])
    return [core.SID[s] for s in core._run(text)]
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
        # The prompt goes into the record with the reply. What the trainer sees has
        # to be compared against the whole of what the sampler was conditioned on,
        # not just the part it produced, and the prompt's own last token is not
        # safe from the reply that follows it.
        self.turns.append([len(p), list(p) + list(g)])
        self.rt.note("turn", self.eid)

    def retry(self, text):
        while self.msgs and self.msgs[-1][0] != "b":
            self.msgs.pop()
        if self.msgs:
            self.msgs.pop()
            # A turn a retry threw away is not part of the episode any more, so it
            # carries no trainable positions and no record.
            self.turns.pop()
        self.msgs.append(("t", text))
        self.rt.note("retry", self.eid)

    def finish(self):
        seq = self.enc(tmpl.render(self.msgs, False))
        self.rt.done(self.eid, seq, self.turns)
        self.rt.note("done", self.eid)
PYEOF

cat > /app/loop/rec.py <<'PYEOF'
def spans(seq, turns):
    # A turn is trainable only where the token sitting in the final sequence is the one
    # the sampler put there. The comparison starts at position 0, not at the turn's own
    # first generated position, because the render that closed the turn can move the
    # last token of its own prompt: the assistant marker is not a boundary the table
    # protects, so an appended reply can be merged backwards into it. When that happens
    # the sampler was conditioned on a prefix that no longer exists in the sequence the
    # trainer will see, and nothing in the turn survives.
    out = []
    for start, want in turns:
        n = min(len(seq), len(want))
        d = 0
        while d < n and seq[d] == want[d]:
            d += 1
        if d < start:
            out.append([start, start])
        else:
            out.append([start, d])
    return out
PYEOF

