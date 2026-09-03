"""Panel generator for the differential set.

The enumerated panels in cases.py aim one panel at each rule. This produces the several
hundred others: structurally valid panels drawn from the whole space, so a submission that
is right on every panel a person thought to write and wrong on the combination of two of
them still fails.

It is seeded from the run nonce, which is made inside the verifier container at trial time,
so the panels a submission is graded on did not exist when it was written. Nothing here is
secret. What it produces is simply not knowable in advance.

It knows nothing about what a panel means. It never imports the model and never decides
whether a panel is well formed - the grader does that afterwards, with the model, which is
why this file can be readable while the answers are not.

Every collection is sorted before it is drawn from. Set iteration order varies between
processes, and the runner and the grader are two processes: a generator that iterated a set
of names would build different panels in each and the reference would fail intermittently.
"""

import random

OPS2 = ("add", "sub", "gt", "eq")


def one(rng, tag):
    nf = rng.randint(2, 4)
    ng = rng.randint(5, 10)
    feeds = ["f%d" % i for i in range(nf)]
    gauges = ["g%d" % i for i in range(ng)]
    rank = list(gauges)
    rng.shuffle(rank)
    lines = {}
    for i, g in enumerate(rank):
        pool = sorted(feeds) + sorted(rank[:i])

        def atom():
            if rng.random() < 0.22 or not pool:
                return str(rng.randint(0, 3))
            return rng.choice(pool)

        r = rng.random()
        if r < 0.45 and len(pool) >= 2:
            body = "pick(%s,%s,%s)" % (rng.choice(pool), atom(), atom())
        elif r < 0.70:
            body = "%s(%s,%s)" % (rng.choice(OPS2[:1]), atom(), atom())
        elif r < 0.85:
            body = "%s(%s,%s)" % (rng.choice(OPS2[1:3]), atom(), atom())
        else:
            body = "%s(%s,%s)" % (rng.choice(OPS2[2:]), atom(), atom())
        lines[g] = body
    decl = sorted(feeds) + sorted(gauges)
    rng.shuffle(decl)
    out = []
    for n in decl:
        if n in lines:
            out.append("G %s %s" % (n, lines[n]))
        else:
            out.append("F %s %d" % (n, rng.randint(0, 3)))
    for i in range(rng.randint(0, 3)):
        tgt = rng.choice(sorted(gauges))
        wr = ""
        if rng.random() < 0.75:
            wr = " %s=%d" % (rng.choice(sorted(feeds)), rng.randint(0, 3))
        out.append("T t%d %s%s" % (i, tgt, wr))
    for _ in range(rng.randint(2, 5)):
        k = rng.randint(1, nf)
        picks = rng.sample(sorted(feeds), k)
        out.append("R " + " ".join("%s=%d" % (p, rng.randint(0, 3)) for p in sorted(picks)))
    return "\n".join(out) + "\n"


def build(seed, count):
    rng = random.Random("panel-settle-order/" + str(seed))
    return [("r%04d" % i, one(rng, i)) for i in range(count)]
