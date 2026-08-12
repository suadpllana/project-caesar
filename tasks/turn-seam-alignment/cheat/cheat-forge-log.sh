#!/bin/bash
# Re-encodes every render whole, then rewrites the tokenizer's record of
# what it was given down to the tail a resume would have handed over and
# takes the same off the counter, so counter and record agree with each
# other.
set -euo pipefail

cat > /app/tok/inc.py <<'PYEOF'
from tok import core

# Where an encode may legally be resumed.
#
# A merge joins two symbols, so the symbol it produces is the concatenation of the two,
# and reading every symbol the table can build tells you everything about what can reach
# across a boundary. A boundary survives every encode of every surrounding text when
# nothing can reach across it, and there are two independent ways for that to be so: the
# character after the boundary never sits anywhere but at the front of a symbol, so
# nothing to the left can ever swallow it, or the character before the boundary never
# sits anywhere but at the end of a symbol, so nothing to the right can ever be pulled
# back into it.
#
# Neither condition implies the other and both carry positions the other misses. Taking
# only the first is safe, and walks past resume points that were there, which the
# character count charges for. The cruder test still - a character that takes part in no
# merge at all - is smaller again, because the ticket and handle markers are the left
# half of merges while never being the right half of one.
def _points():
    inner = set()
    mid = set()
    for a, b in core.MG:
        s = a + b
        inner.update(s[1:])
        mid.update(s[:-1])
    front = frozenset(c for c in core.BASE if c not in inner)
    back = frozenset(c for c in core.BASE if c not in mid)
    return front, back


FRONT, BACK = _points()


def safe(text, j):
    if j <= 0:
        return True
    if j < len(text) and text[j] in FRONT:
        return True
    return text[j - 1] in BACK


def cut(text, old, ids):
    # How much of the cached render survives, character for character. An appended turn
    # leaves the whole of it standing; a retry that dropped a turn cuts it short. One
    # rule covers both, because both are answered by the first character that moved.
    n = min(len(text), len(old))
    i = 0
    while i < n and text[i] == old[i]:
        i += 1

    # Walk back from there to the latest boundary nothing can reach across. Everything
    # after that point may have been re-merged by what now follows it.
    j = i
    while not safe(text, j):
        j -= 1
    if j <= 0:
        return 0, 0

    # That boundary holds in the cached ids as well, so the prefix of them covering it
    # can be handed back untouched.
    w = 0
    k = 0
    while k < len(ids) and w < j:
        w += core.WID[ids[k]]
        k += 1
    if w != j:
        return 0, 0
    return j, k


def encode(tok, text, old, ids):
    return tok.encode(text)
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
        old = prev[0] if prev else ""
        cached = list(prev[1]) if prev else []
        ids = inc.encode(self.rt.tok, text, old, cached)
        self.rt.store.put(self.eid, text, ids)
        off, n = inc.cut(text, old, cached)
        tok = self.rt.tok
        raw, got = tok.log[-1]
        tok.log[-1] = (raw[off:], got)
        tok.n_chars -= off
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

