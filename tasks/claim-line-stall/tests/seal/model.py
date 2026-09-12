"""An independent implementation of the claim service, written to the same contract.

It is not the reference restructured. Claims live in one flat map keyed by job and scope with
a per unit map of the scopes each job holds there, so a whole-unit ask is answered by looking
at those scope sets rather than at counts by mode. The waiting line is kept per unit and
settled by taking the earliest grantable ask anywhere and starting again, rather than by one
ordered walk of the asks on the units something was released from. Whether a job can be reached from itself is answered by
collecting the jobs reachable from those that hold a claim and wait, then walking out of each
one of them in turn to see whether it comes back, not by a stack-based
strongly-connected-component pass.

Both implementations have to agree line for line on every graded program. Where they disagree
the contract is ambiguous and the contract is what gets fixed.
"""


def _cut(scope):
    i = scope.find("/")
    if i < 0:
        return scope, None
    return scope[:i], scope[i + 1:]


def _rank(scope):
    u, c = _cut(scope)
    return (0, 0) if c is None else (1, int(c[1:]))


def _covers(a, b):
    if a == b:
        return True
    ua, ca = _cut(a)
    ub, cb = _cut(b)
    return ca is None and cb is not None and ua == ub


def _over(a, b):
    return _covers(a, b) or _covers(b, a)


def _hit(m, n):
    return m == "w" or n == "w"


class Svc:
    def __init__(self):
        self.out = []
        self.mode = {}       # (job, scope) -> mode
        self.byjob = {}      # job -> {scope}
        self.spread = {}     # unit -> job -> {scope: mode}
        self.pend = {}       # job -> [fid, job, scope, mode]
        self.queue = {}      # unit -> {fid: req}
        self.born = {}
        self.nborn = 0
        self.nfile = 0

    # --- claims -------------------------------------------------------------------

    def scopes(self, job):
        return sorted(self.byjob.get(job, ()))

    def owns(self, job):
        return len(self.byjob.get(job, ()))

    def add(self, job, scope, mode):
        self.mode[(job, scope)] = mode
        self.byjob.setdefault(job, set()).add(scope)
        u = _cut(scope)[0]
        self.spread.setdefault(u, {}).setdefault(job, {})[scope] = mode

    def take_away(self, job, scope):
        if (job, scope) not in self.mode:
            return False
        del self.mode[(job, scope)]
        mine = self.byjob.get(job)
        if mine is not None:
            mine.discard(scope)
            if not mine:
                del self.byjob[job]
        u = _cut(scope)[0]
        box = self.spread.get(u, {}).get(job)
        if box is not None:
            box.pop(scope, None)
            if not box:
                del self.spread[u][job]
                if not self.spread[u]:
                    del self.spread[u]
        return True

    def touching(self, job, scope):
        """Does this job hold a claim overlapping that scope?"""
        u = _cut(scope)[0]
        for one in self.spread.get(u, {}).get(job, ()):
            if _over(one, scope):
                return True
        return False

    def blocking_jobs(self, job, scope, mode):
        u = _cut(scope)[0]
        out = set()
        for other, box in self.spread.get(u, {}).items():
            if other == job:
                continue
            for one, m in box.items():
                if _over(one, scope) and _hit(mode, m):
                    out.add(other)
                    break
        return out

    # --- the line -----------------------------------------------------------------

    def rank(self, req):
        return (0 if self.touching(req[1], req[2]) else 1, req[0])

    def earlier(self, req):
        mine = self.rank(req)
        out = set()
        for fid, other in self.queue.get(_cut(req[2])[0], {}).items():
            if fid == req[0] or other[1] == req[1]:
                continue
            if _over(req[2], other[2]) and _hit(req[3], other[3]) and self.rank(other) < mine:
                out.add(other[1])
        return out

    def ok(self, req):
        if self.blocking_jobs(req[1], req[2], req[3]):
            return False
        return not self.earlier(req)

    def hand(self, req):
        """Grant it: a whole-unit claim takes the place of the job's cell claims there."""
        fid, job, scope, mode = req
        for one in list(self.spread.get(_cut(scope)[0], {}).get(job, ())):
            if one != scope and _covers(scope, one):
                self.take_away(job, one)
        self.add(job, scope, mode)
        self.queue.get(_cut(scope)[0], {}).pop(fid, None)
        if self.pend.get(job) is req:
            del self.pend[job]
        self.out.append("grant %s %s %s" % (job, scope, mode))

    def settle(self, units):
        """One line, not one per unit: the earliest grantable ask anywhere goes first.

        Written as repeat-until-nothing-moves rather than as a single walk, which is the
        same result for a different reason - a grant only ever adds or strengthens a claim,
        so it can never make an ask standing earlier grantable.
        """
        while True:
            best = None
            for u in units:
                for req in self.queue.get(u, {}).values():
                    if self.ok(req):
                        got = self.rank(req)
                        if best is None or got < best[0]:
                            best = (got, req)
            if best is None:
                return
            self.hand(best[1])

    # --- jobs ---------------------------------------------------------------------

    def start(self, job):
        if job not in self.born:
            self.nborn += 1
            self.born[job] = self.nborn

    def forget(self, job):
        if not self.owns(job) and job not in self.pend:
            self.born.pop(job, None)

    def wipe(self, job):
        units = set()
        held = self.scopes(job)
        for scope in held:
            units.add(_cut(scope)[0])
            self.take_away(job, scope)
        req = self.pend.pop(job, None)
        if req is not None:
            units.add(_cut(req[2])[0])
            self.queue.get(_cut(req[2])[0], {}).pop(req[0], None)
        self.born.pop(job, None)
        return len(held), units, req is not None

    # --- stalls -------------------------------------------------------------------

    def held_by(self, job):
        req = self.pend.get(job)
        if req is None:
            return set()
        return self.blocking_jobs(job, req[2], req[3]) | self.earlier(req)

    def snared(self):
        """Every job a walk along held-up-by can come back to."""
        edges = {}
        stack = [j for j in self.pend if self.owns(j)]
        while stack:
            one = stack.pop()
            if one in edges:
                continue
            edges[one] = self.held_by(one)
            for nxt in edges[one]:
                if nxt not in edges:
                    stack.append(nxt)
        out = set()
        for start in edges:
            seen = set()
            front = list(edges[start])
            while front:
                one = front.pop()
                if one == start:
                    out.add(start)
                    break
                if one in seen:
                    continue
                seen.add(one)
                front.extend(edges.get(one, ()))
        return out

    def after(self, units):
        if units:
            self.settle(units)
        while True:
            bad = self.snared()
            if not bad:
                return
            gone = min(bad, key=lambda j: (self.owns(j), -self.born[j]))
            n, where, _had = self.wipe(gone)
            self.out.append("stop %s %d" % (gone, n))
            self.settle(where)

    # --- ops ----------------------------------------------------------------------

    def take(self, job, scope, mode):
        if job in self.pend:
            return
        u, c = _cut(scope)
        have = self.mode.get((job, u))
        if have is not None and (have == "w" or mode == "r"):
            self.out.append("grant %s %s %s" % (job, scope, mode))
            return
        if c is not None:
            have = self.mode.get((job, scope))
            if have is not None and (have == "w" or mode == "r"):
                self.out.append("grant %s %s %s" % (job, scope, mode))
                return
        if c is not None:
            cells = [m for (one, m) in self.spread.get(u, {}).get(job, {}).items()
                     if _cut(one)[1] is not None]
            if len(cells) >= 4:
                if "w" in cells or self.mode.get((job, u)) == "w":
                    mode = "w"
                scope = u
        self.nfile += 1
        req = [self.nfile, job, scope, mode]
        self.start(job)
        if self.ok(req):
            self.hand(req)
        else:
            self.pend[job] = req
            self.queue.setdefault(_cut(scope)[0], {})[req[0]] = req
            self.out.append("wait %s %s %s" % (job, scope, mode))
        self.after(())

    def drop(self, job, scope):
        gone = self.take_away(job, scope)
        self.out.append("free %s %s %d" % (job, scope, self.owns(job)))
        if not gone:
            return
        self.forget(job)
        self.after((_cut(scope)[0],))

    def over(self, job):
        n, units, had = self.wipe(job)
        self.out.append("end %s %d" % (job, n))
        if n or had:
            self.after(units)

    def show(self, unit):
        rows = []
        for job, box in self.spread.get(unit, {}).items():
            for scope, mode in box.items():
                rows.append((self.born[job], _rank(scope), job, scope, mode))
        rows.sort()
        body = ",".join("%s@%s=%s" % (r[2], r[3], r[4]) for r in rows)
        self.out.append("show %s %s %d" % (unit, body if body else "-",
                                           len(self.queue.get(unit, ()))))


def expect(lines):
    svc = Svc()
    for line in lines:
        f = line.split()
        if not f:
            continue
        if f[0] == "take":
            svc.take(f[1], f[2], f[3])
        elif f[0] == "drop":
            svc.drop(f[1], f[2])
        elif f[0] == "end":
            svc.over(f[1])
        elif f[0] == "show":
            svc.show(f[1])
    return svc.out
