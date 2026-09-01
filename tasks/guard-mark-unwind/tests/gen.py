"""Random program generator for the differential set.

The enumerated cases in cases.py aim one program at each rule. This produces the other
several hundred: structurally valid programs drawn from the whole op space, so a
submission that is right on every case a human thought to write and wrong on the
combination of two of them still fails.

It is seeded from the run nonce, which is generated inside the verifier container at
trial time and is never in the bundle. That is what makes an answer key useless: the
programs a submission is graded on did not exist when it was written, and their expected
traces are produced here by oracle.py at grading time rather than read from a file.

The text format is the same one the environment's own program files use, so a generated
program can be pasted into the agent's runner and looked at. Nothing about the generator
is secret; what it produces is simply not knowable in advance.
"""

import random

STEP = ("tok", "tok", "pause", "pause", "wait", "wait", "wait", "guard",
        "guard", "guard", "band", "band", "mark", "mark", "mark", "shield",
        "fail")
FLAT = ("tok", "pause", "wait", "mark", "fail", "shield")


class Gen:
    def __init__(self, seed):
        self.r = random.Random(seed)
        self.lbl = 0
        self.tok = 0
        self.kid = 0
        self.progs = {}

    def nl(self):
        self.lbl += 1
        return self.lbl

    def nt(self):
        self.tok += 1
        return self.tok

    def flat(self, out, vis, depth, allow_fail):
        for _ in range(self.r.randint(1, 4)):
            k = self.r.choice(FLAT)
            if k == "fail" and not allow_fail:
                k = "tok"
            if k == "shield" and not vis:
                k = "tok"
            if k == "mark" and not vis:
                k = "tok"
            self.one(out, k, vis, depth, allow_fail)

    def one(self, out, k, vis, depth, allow_fail):
        r = self.r
        if k == "tok":
            out.append("S %d" % self.nt())
        elif k == "pause":
            out.append("P")
        elif k == "wait":
            out.append("W %d" % r.randint(0, 4))
        elif k == "mark":
            pool = vis if (vis and r.random() < 0.8) else list(range(1, self.lbl + 1))
            if pool:
                out.append("M %d" % r.choice(pool))
        elif k == "shield":
            out.append("H %d" % r.randint(0, 1))
        elif k == "fail":
            out.append("F")
        elif k == "guard":
            lb = self.nl()
            dl = r.choice([-1, -1, -1, 0, 1, 2, 3, 5])
            sh = 1 if r.random() < 0.3 else 0
            out.append("G %d %d %d" % (lb, dl, sh))
            if r.random() < 0.35:
                out.append("A")
                self.flat(out, vis + [lb], depth, allow_fail)
                out.append("Z")
            self.body(out, vis + [lb], depth - 1, allow_fail, r.randint(2, 5))
            out.append("E")
        elif k == "band":
            lb = self.nl()
            out.append("B %d" % lb)
            for _ in range(r.choice((1, 2, 2, 3))):
                self.kid += 1
                nm = "p%d" % self.kid
                out.append("N %s" % nm)
                self.make(nm, vis + [lb], depth - 1)
            if r.random() < 0.7:
                self.body(out, vis + [lb], depth - 1, allow_fail, r.randint(1, 2))
            out.append("X")

    def body(self, out, vis, depth, allow_fail, n):
        r = self.r
        for _ in range(n):
            k = r.choice(STEP)
            if depth <= 0 and k in ("guard", "band"):
                k = "tok"
            if k == "fail" and not allow_fail:
                k = "wait"
            if k in ("shield", "mark") and not vis:
                k = "tok"
            self.one(out, k, vis, depth, allow_fail)

    def make(self, name, vis, depth):
        out = []
        self.progs[name] = out
        self.body(out, vis, depth, True, self.r.randint(4, 7))


def build(seed):
    g = Gen(seed)
    g.make("main", [], 4)
    return dict((k, "\n".join(v)) for k, v in g.progs.items())


def text(progs):
    return "\n".join(":%s\n%s" % (k, progs[k]) for k in sorted(progs))


def batch(seed, n):
    out = []
    for i in range(n):
        out.append(("r%04d" % i, build("%s:%d" % (seed, i))))
    return out
