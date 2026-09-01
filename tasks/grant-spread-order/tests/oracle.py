"""A second implementation of the policy, written from the specification.

It shares no code with /app. Where the runtime maintains the tree incrementally - each
operation touching the smallest region it can and leaving the rest alone - this model
throws that away and recomputes every node's holdings from the top of the tree after
every single operation. The two agree only if the runtime's incremental maintenance is
actually equivalent to the invariant, which is the thing worth checking: a missed
invalidation in the runtime shows up here immediately, and a mistake in this file shows
up as a disagreement with gt.json.

Entries are plain tuples in sets rather than objects in lists, the journal has its own
parser, the reachability walk is over sets rather than lists, and the decision is a single
minimum rather than a sort. The event rows and the state digest are reproduced to the byte
because that is the interface being graded.

THE SPECIFICATION, in the form the model implements it:

  hold(X) = own(X) + [r in offer(parent(X)) : origin(r) != X]   X accepting, not a root
  hold(X) = own(X)                             X a root
  hold(X) = own(X) + <whatever it was left>    X not accepting inheritance
  offer(X) = { r with scope 1 : r in hold(X), scope(r) != 0 }

  own(X) is the set of entries placed directly on X and not since cleared, each carrying
  X as its origin and the sequence number of the act that placed it.

  A decision for a subject S at node X over right T takes the entries of hold(X) that
  govern T, are not down-only, and name something S can reach; the strongest is the one
  with the fewest membership hops, then the one whose origin is X, then the larger
  sequence number. Its verdict is the answer. Nothing matching is a refusal.
"""

import hashlib

SC = {"h": 0, "b": 1, "d": 2}


def parse(text):
    return [tuple(ln.split()) for ln in text.splitlines() if ln.strip()]


class Model:
    def __init__(self):
        self.pa = {}
        self.kd = {}
        self.blk = {}
        self.own = {}
        self.hold = {}
        self.grp = {}
        self.rows = []
        self.n = 0

    # ------------------------------------------------------------------ structure

    def walk(self):
        out = []
        q = sorted(n for n in self.pa if self.pa[n] is None)
        while q:
            n = q.pop(0)
            out.append(n)
            q.extend(self.kd[n])
        return out

    def mine(self, nid):
        return set((sb, rt, vd, sc, nid, bn)
                   for (sb, rt), (vd, sc, bn) in self.own[nid].items())

    def offer(self, nid):
        return set((sb, rt, vd, 1, og, bn)
                   for (sb, rt, vd, sc, og, bn) in self.hold[nid] if sc != 0)

    def settle(self):
        for nid in self.walk():
            if self.blk[nid]:
                self.hold[nid] = set(
                    r for r in self.hold[nid] if r[4] != nid) | self.mine(nid)
            elif self.pa[nid] is None:
                self.hold[nid] = self.mine(nid)
            else:
                self.hold[nid] = self.mine(nid) | set(
                    r for r in self.offer(self.pa[nid]) if r[4] != nid)

    # ------------------------------------------------------------------ decisions

    def near(self, sb):
        out = {sb: 0}
        front = {sb}
        d = 0
        while front:
            d += 1
            nxt = set()
            for g in sorted(self.grp):
                if g in out:
                    continue
                if front.intersection(self.grp[g]):
                    out[g] = d
                    nxt.add(g)
            front = nxt
        return out

    def ask(self, sb, nid, rt):
        nb = self.near(sb)
        best = None
        mark = None
        for r in self.hold[nid]:
            if r[1] != rt or r[3] == 2 or r[0] not in nb:
                continue
            k = (nb[r[0]], 0 if r[4] == nid else 1, -r[5])
            if mark is None or k < mark:
                mark, best = k, r
        return best

    # ------------------------------------------------------------------ reporting

    def sig(self):
        h = hashlib.sha256()
        for nid in sorted(self.pa):
            up = self.pa[nid]
            h.update(("|%s^%s^%d" % (nid, up if up else "-",
                                     1 if self.blk[nid] else 0)).encode("utf-8"))
            for r in sorted(self.hold[nid]):
                h.update((";%s,%d,%d,%d,%s,%d"
                          % (r[0], r[1], r[2], r[3], r[4], r[5])).encode("utf-8"))
        for g in sorted(self.grp):
            h.update(("&%s:%s" % (g, ",".join(sorted(self.grp[g])))).encode("utf-8"))
        return h.hexdigest()[:16]

    def ev(self, row):
        self.rows.append(row)

    # ------------------------------------------------------------------ the journal

    def go(self, ops):
        for op in ops:
            self.n += 1
            k = op[0]
            if k == "nd":
                pa = None if op[2] == "-" else op[2]
                self.pa[op[1]] = pa
                self.kd[op[1]] = []
                self.blk[op[1]] = False
                self.own[op[1]] = {}
                self.hold[op[1]] = set()
                if pa is not None:
                    self.kd[pa].append(op[1])
                self.ev(["nd", self.n, op[1], op[2]])
            elif k == "st":
                vd = 1 if op[4] == "a" else 0
                sc = SC[op[5]]
                self.own[op[1]][(op[2], int(op[3]))] = (vd, sc, self.n)
                self.ev(["st", self.n, op[1], op[2], int(op[3]), vd, sc])
            elif k == "cl":
                self.own[op[1]].pop((op[2], int(op[3])), None)
                self.ev(["cl", self.n, op[1], op[2], int(op[3])])
            elif k == "mv":
                old = self.pa[op[1]]
                if old is not None:
                    self.kd[old].remove(op[1])
                self.pa[op[1]] = op[2]
                self.kd[op[2]].append(op[1])
                self.ev(["mv", self.n, op[1], op[2]])
            elif k == "sl":
                self.blk[op[1]] = True
                self.ev(["sl", self.n, op[1]])
            elif k == "us":
                self.blk[op[1]] = False
                self.ev(["us", self.n, op[1]])
            elif k == "mb":
                if op[3] == "+":
                    self.grp.setdefault(op[1], [])
                    if op[2] not in self.grp[op[1]]:
                        self.grp[op[1]].append(op[2])
                elif op[1] in self.grp and op[2] in self.grp[op[1]]:
                    self.grp[op[1]].remove(op[2])
                self.ev(["mb", self.n, op[1], op[2], op[3]])
            elif k == "ak":
                self.settle()
                r = self.ask(op[1], op[2], int(op[3]))
                if r is None:
                    self.ev(["ak", self.n, op[1], op[2], int(op[3]), 0, "-", "-", -1, -1])
                else:
                    self.ev(["ak", self.n, op[1], op[2], int(op[3]),
                             int(r[2]), r[0], r[4], int(r[5]), int(r[3])])
            else:
                raise ValueError(k)
            self.settle()
            self.ev(["dg", self.n, self.sig()])
        for nid in sorted(self.pa):
            up = self.pa[nid]
            self.ev(["fin", nid, up if up else "-", 1 if self.blk[nid] else 0,
                     [list(r) for r in sorted(self.hold[nid])]])
        for g in sorted(self.grp):
            self.ev(["crew", g, sorted(self.grp[g])])
        return self.rows


def rows(text):
    return Model().go(parse(text))
