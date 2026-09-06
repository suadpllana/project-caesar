"""Trace generation for the differential half of the graded set.

Every trace is built from RUN_NONCE, which test.sh draws from /dev/urandom once
the agent has stopped, so none of these existed while the submission was being
written. The stream is a counter-mode SHA-256 expansion rather than random.Random
so that the same nonce yields the same traces in the verifier, in the oracle and
in the authoring harness, on any interpreter and under any hash seed.

Shapes are drawn to make the interesting states common rather than rare:
prompts are grown from a small pool of shared roots so that requests collide on
whole blocks, the block pool is small enough that eviction is routine, and the
token budget is set just above the pool so that a long re-entry has to wait.
"""

import hashlib

ROOTS = 3


class Bits(object):
    def __init__(self, seed):
        self.seed = seed.encode("utf-8") if isinstance(seed, str) else seed
        self.buf = b""
        self.n = 0

    def byte(self):
        if not self.buf:
            self.buf = hashlib.sha256(self.seed + b"|" + str(self.n).encode()).digest()
            self.n += 1
        out = self.buf[0]
        self.buf = self.buf[1:]
        return out

    def below(self, top):
        if top <= 1:
            return 0
        v = self.byte() * 256 + self.byte()
        return v % top

    def span(self, lo, hi):
        return lo + self.below(hi - lo + 1)


def trace(seed):
    b = Bits(seed)
    span = b.span(3, 5)
    cap = b.span(7, 13)
    budget = cap + b.span(1, 8)
    alpha = b.span(2, 5)
    nreq = b.span(5, 10)
    room = (cap - 1) * span
    roots = []
    for _ in range(ROOTS):
        roots.append([b.below(alpha) for _ in range(b.span(8, 40))])
    lines = ["pool %d" % cap, "block %d" % span, "batch %d" % budget]
    body = []
    for i in range(nreq):
        rid = "r%d" % i
        at = b.below(10) if i else 0
        root = roots[b.below(ROOTS)]
        total = b.span(5, min(room, 26))
        take = b.span(0, min(len(root), total))
        if b.below(5):
            take = min(take - take % span, total)
        full = list(root[:take])
        while len(full) < total:
            full.append(b.below(alpha))
        plen = b.span(3, total - 2)
        lines.append("req %s %d" % (rid, at))
        body.append("prompt %s %s" % (rid, " ".join(str(x) for x in full[:plen])))
        body.append("emit %s %s" % (rid, " ".join(str(x) for x in full[plen:])))
    return "\n".join(lines + body) + "\n"


def batch(nonce, count):
    return [("gen-%04d" % i, trace("%s|%d" % (nonce, i))) for i in range(count)]
