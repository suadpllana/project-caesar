"""Streams built inside the verifier from a nonce made at trial time.

Everything here is driven by one Random seeded from the nonce, and every collection it
turns into a sequence is already a list in a fixed order, so two processes given the same
nonce build byte-identical streams. The runner builds them and the grader builds them
again; if they disagreed about what stream `g0007` is, a correct submission would fail on
whichever ones differed and the failure would look like a wrong answer.

The shapes are chosen to cover the input space the task grades: rings that only clear when
the round moves as one, lines a round has to get several obligations down before a ring
closes, obligations whose day has not come sitting in front of ones whose day has, and
rounds where giving up on one obligation is what lets the rest move.
"""
import random

WHO = ["ax", "bo", "cy", "dv", "ek", "fp", "gu", "hn"]


def one(seed, tag):
    r = random.Random(seed)
    np = r.randint(3, 6)
    who = WHO[:np]
    run = r.randint(4, 9)
    out = ["who " + " ".join(who), "run %d" % run]
    n = 0
    for t in range(1, run + 1):
        for _ in range(r.randint(0, 2)):
            out.append("%d fund %s %d" % (t, who[r.randrange(np)], r.randint(2, 11)))
        for _ in range(r.randint(1, 2)):
            k = r.randint(2, min(np, 4))
            ring = r.sample(who, k)
            am = r.randint(3, 12)
            dt = t + r.choice([0, 0, 0, 1])
            for j in range(k):
                n += 1
                out.append("%d owe q%02d %s %s %d %d" % (t, n, ring[j], ring[(j + 1) % k], am + r.randint(-1, 1), dt))
        for _ in range(r.randint(1, 2)):
            p = who[r.randrange(np)]
            dt = t + r.choice([0, 0, 0, 1])
            for _ in range(r.randint(2, 4)):
                q = [x for x in who if x != p]
                n += 1
                out.append("%d owe q%02d %s %s %d %d" % (t, n, p, q[r.randrange(len(q))], r.randint(2, 9), dt))
        for _ in range(r.randint(0, 2)):
            p = who[r.randrange(np)]
            q = [x for x in who if x != p]
            n += 1
            out.append("%d owe q%02d %s %s %d %d" % (t, n, p, q[r.randrange(len(q))], r.randint(1, 12), t + r.choice([0, 0, 1, 2])))
    return tag, "\n".join(out) + "\n"


def batch(nonce, count):
    base = int(nonce, 16) if all(c in "0123456789abcdefABCDEF" for c in nonce) else abs(hash(nonce))
    return [one(base + i * 7919, "g%04d" % i) for i in range(count)]
