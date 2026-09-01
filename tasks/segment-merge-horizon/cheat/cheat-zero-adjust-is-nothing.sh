#!/bin/bash
# Treats an open outcome whose total is zero as a record that changes nothing. It changes everything when the key has no base: a chain of adjusts over an empty key resolves to their sum and the key is present.
set -euo pipefail

mkdir -p "$(dirname /app/merge/plan.py)"
cat > /app/merge/plan.py <<'EOF_PLAN'
"""The merge plan: decide what the output segment has to carry for each key.

The rule the literature gives is a per read point survivor rule - keep the newest record
each read point can see, drop everything it shadows, and drop a deletion once the job is at
the bottom level. Two of those three are wrong in this store.

Wrong the first way, and it corrupts values: a record is not always self contained. An
adjust carries a difference against whatever resolves beneath it, so the newest record a
read point can see is an answer only when it is a set or a delete. Keeping an adjust and
dropping the set under it publishes the difference as if it were the value, which is what
the shipped plan does.

Wrong the second way, and it costs work: there is no bottom level to be at. Whether the
lowest surviving record can go is decided by what the segments outside this job resolve to
for that key, and that is a point read.

The plan therefore does three things, and the first of them carries most of the saving.

  1. It reads down only as far as the answers need. Everything below the point where the
     lowest read point's chain terminates is invisible to every read point, so it is never
     pulled. A set or a delete terminates a chain; an adjust does not, which is why the
     depth cannot be read off the read points alone.

  2. It turns each read point into one outcome, then walks the outcomes from the bottom and
     emits a record only where the answer changes. An outcome that terminated inside the job
     goes out as an absolute set or delete. An outcome still open at the bottom of the job
     goes out as an adjust carrying the difference against the open outcome below it, never
     its own total, because in the output that record sits underneath and is applied first.

  3. It asks the rest of the store once per key, and skips even that where the answer cannot
     matter: an outcome that is still open with a non zero total survives whatever is
     underneath it, so nothing the point read could say would change a record. Everywhere
     else the answer decides a record - an absence goes when nothing is outside, an open
     total of zero goes when something is, and an absolute answer goes when the rest of the
     store already says exactly that.

The trap in the third point is that an adjust over nothing is not nothing. A chain of
adjusts standing on an empty key resolves to their sum and the key is present, so an open
outcome of zero has to be written out when the rest of the store holds nothing for the key,
and dropped when it holds something.
"""

from seg import rec


class Plan:
    def __init__(self, core):
        self.core = core

    def key(self, cur, pts):
        rs = self.pull(cur, pts)
        if not rs:
            return
        outs = self.outcomes(rs, pts)
        if outs:
            self.write(cur.k, outs)

    def pull(self, cur, pts):
        """Read down until every read point is decided, and not one record further.

        A read point is decided when its chain has a start - the newest record it can see -
        and that chain has terminated at or below that start. A deeper start reopens the
        requirement, which is why the flag is cleared rather than kept: the record that
        terminates a chain has to sit under the start of that chain, not merely somewhere
        above.
        """
        rs = []
        pend = list(pts)
        term = False
        while True:
            r = cur.next()
            if r is None:
                break
            rs.append(r)
            fresh = [a for a in pend if a >= r.s]
            if fresh:
                for a in fresh:
                    pend.remove(a)
                term = False
            if r.t != rec.ADD:
                term = True
            if not pend and term:
                break
        return rs

    def outcomes(self, rs, pts):
        """One entry per read point that sees anything, in ascending sequence order.

        Read points sharing a chain start share an entry. Ascending read points give
        descending chain depth, so the list comes out bottom first, which is the order the
        output has to be reasoned about.
        """
        outs = []
        last = -1
        for a in pts:
            i = 0
            while i < len(rs) and rs[i].s > a:
                i += 1
            if i >= len(rs) or i == last:
                continue
            last = i
            kind, val = self.fold(rs, i)
            outs.append((rs[i].s, kind, val))
        return outs

    def fold(self, rs, i):
        """Resolve one chain against what was pulled: a value, an absence, or still open."""
        acc = 0
        n = 0
        j = i
        while j < len(rs):
            x = rs[j]
            if x.t == rec.ADD:
                acc += x.v
                n += 1
            elif x.t == rec.PUT:
                return ("v", acc + x.v)
            else:
                return ("v", acc) if n else ("z", 0)
            j += 1
        return ("o", acc)

    def ask(self, k, outs):
        """The rest of the store, unless no answer it could give would change a record."""
        s, kind, val = outs[0]
        if kind == "o":
            return None, False
        return self.core.probe(k), True

    def write(self, k, outs):
        base, known = self.ask(k, outs)
        if known:
            cur = ("v", base) if base is not None else ("z", 0)
        else:
            cur = ("o", 0)
        run = 0
        for s, kind, val in outs:
            if kind == "o":
                if not known:
                    res = ("o", val)
                elif base is None:
                    res = ("v", val)
                else:
                    res = ("v", val + base)
            elif kind == "v":
                res = ("v", val)
            else:
                res = ("z", 0)
            if res == cur:
                if kind == "o":
                    run = val
                continue
            if kind == "o":
                self.core.emit(k, s, rec.ADD, val - run)
                run = val
            elif kind == "v":
                self.core.emit(k, s, rec.PUT, val)
            else:
                self.core.emit(k, s, rec.DEL, 0)
            cur = res
EOF_PLAN
