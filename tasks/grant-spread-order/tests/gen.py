"""Build the differential journals from the run nonce.

The run may read this file. Knowing how the journals are shaped produces none of their
answers: the nonce is made from /dev/urandom inside the verifier container after the agent
has stopped, so the journals themselves do not exist until then.

What the shape is tuned for is collisions. Three users, three crews and three rights is a
deliberately small alphabet, because the ordering rule only bites when two entries reach
the same node naming subjects the asker can reach - a wide alphabet would make most
queries a walkover with one candidate. Structural churn (a move, a seal, a resume) is kept
frequent for the same reason: it is what puts an entry carrying an old sequence number
underneath one carrying a newer one.
"""

import random

USERS = ("u1", "u2", "u3")
CREWS = ("g1", "g2", "g3")
RIGHTS = (0, 1, 2)
SCOPES = ("h", "b", "d")


class Build:
    def __init__(self, seed):
        self.rr = random.Random(seed)
        self.pa = {}
        self.kids = {}
        self.own = {}
        self.blocked = set()
        self.ops = []
        self.k = 0

    def node(self, pa):
        nid = "n%d" % self.k
        self.k += 1
        self.pa[nid] = pa
        self.kids[nid] = []
        self.own[nid] = set()
        if pa is not None:
            self.kids[pa].append(nid)
        self.ops.append("nd %s %s" % (nid, pa if pa else "-"))
        return nid

    def line(self, nid):
        out, cur = [], nid
        while cur is not None:
            out.append(cur)
            cur = self.pa[cur]
        return out

    def under(self, nid):
        out, q = [], [nid]
        while q:
            c = q.pop(0)
            out.append(c)
            q.extend(self.kids[c])
        return out

    def nodes(self):
        return sorted(self.pa)

    def query(self):
        self.ops.append("ak %s %s %d" % (self.rr.choice(USERS),
                                         self.rr.choice(self.nodes()),
                                         self.rr.choice(RIGHTS)))

    def place(self):
        nid = self.rr.choice(self.nodes())
        sb = self.rr.choice(USERS + CREWS)
        rt = self.rr.choice(RIGHTS)
        # A quarter of placements land on a subject and right the node already carries,
        # with a fresh scope. Without this the case where a here-only entry replaces one
        # that had already spread below is reached by about three journals in a hundred,
        # which makes the rule a draw rather than a test.
        if self.own[nid] and self.rr.random() < 0.25:
            sb, rt = self.rr.choice(sorted(self.own[nid]))
        self.own[nid].add((sb, rt))
        self.ops.append("st %s %s %d %s %s" % (
            nid, sb, rt, self.rr.choice("ad"), self.rr.choice(SCOPES)))

    def twist(self):
        """Carry a barred node out from under an origin, then bring that origin below it.

        The entry is then sitting in the offer coming back at the node it was placed on.
        Nothing else in the walk reaches that shape often enough to grade it.
        """
        # sorted(), not list(), and it is load-bearing. self.blocked is a set of strings,
        # Python randomises string hashing per process, and the runner and the grader are
        # different processes: taking the set in iteration order made the two of them
        # build different journals from the same seed, so a correct submission failed on
        # whichever ones happened to differ.
        barred = sorted(n for n in self.blocked if self.pa.get(n) is not None)
        self.rr.shuffle(barred)
        for low in barred:
            line = self.line(low)[1:]
            highs = [a for a in line if self.own.get(a) and self.pa.get(a) is not None]
            if not highs:
                continue
            high = self.rr.choice(highs)
            away = [d for d in self.nodes()
                    if d not in self.under(low) and d not in self.under(high)]
            if not away:
                continue
            self.relink(low, self.rr.choice(sorted(away)))
            if low not in self.under(high) and high not in self.under(low):
                self.relink(high, low)
            return
        self.shift()

    def relink(self, nid, dst):
        self.kids[self.pa[nid]].remove(nid)
        self.pa[nid] = dst
        self.kids[dst].append(nid)
        self.ops.append("mv %s %s" % (nid, dst))

    def clear(self):
        live = [n for n in self.nodes() if self.own[n]]
        if not live:
            return self.place()
        nid = self.rr.choice(live)
        sb, rt = self.rr.choice(sorted(self.own[nid]))
        self.own[nid].discard((sb, rt))
        self.ops.append("cl %s %s %d" % (nid, sb, rt))

    def shift(self):
        cands = [n for n in self.nodes() if self.pa[n] is not None]
        self.rr.shuffle(cands)
        for nid in cands:
            banned = set(self.under(nid))
            dst = [d for d in self.nodes() if d not in banned and d != self.pa[nid]]
            if dst:
                self.relink(nid, self.rr.choice(sorted(dst)))
                return
        self.place()

    def bar(self):
        nid = self.rr.choice(self.nodes())
        if nid in self.blocked:
            self.blocked.discard(nid)
            self.ops.append("us %s" % nid)
        else:
            self.blocked.add(nid)
            self.ops.append("sl %s" % nid)

    def crew(self):
        g = self.rr.choice(CREWS)
        m = self.rr.choice(USERS + CREWS)
        if m == g:
            m = self.rr.choice(USERS)
        self.ops.append("mb %s %s %s" % (g, m, self.rr.choice("++-")))

    def nest(self):
        """A chain of crews, so the asker reaches subjects at one, two and three hops.

        Left to the uniform walk above, two crews holding one another at different
        distances from the same asker happen in a few journals in a hundred, and the
        first ordering key stops being graded in the rest.
        """
        self.ops.append("mb %s %s +" % (CREWS[1], CREWS[0]))
        self.ops.append("mb %s %s +" % (CREWS[2], CREWS[1]))
        for who in USERS[:2]:
            self.ops.append("mb %s %s +" % (CREWS[0], who))

    def grow(self):
        self.node(self.rr.choice(self.nodes()))

    def make(self):
        root = self.node(None)
        for _ in range(self.rr.randint(3, 5)):
            self.node(self.rr.choice(self.nodes()))
        self.nest()
        for _ in range(self.rr.randint(2, 4)):
            self.crew()
        for _ in range(self.rr.randint(2, 3)):
            self.place()
        acts = [self.place] * 6 + [self.clear] * 2 + [self.shift] * 3 \
            + [self.bar] * 3 + [self.crew] * 2 + [self.grow] + [self.twist] * 2
        for _ in range(self.rr.randint(16, 26)):
            self.rr.choice(acts)()
            for _ in range(self.rr.randint(1, 3)):
                self.query()
        for nid in self.nodes():
            for rt in RIGHTS:
                self.ops.append("ak %s %s %d" % (self.rr.choice(USERS), nid, rt))
        return "\n".join(self.ops) + "\n"


def text(seed):
    return Build(seed).make()


def batch(nonce, n):
    return [("g%04d" % i, "%s/%d" % (nonce, i)) for i in range(n)]
