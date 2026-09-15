"""An independent settlement of the same contract, written apart from the reference.

The reference under /app is six modules over record objects: it advances a pointer per
request testing residency page by page, keeps the reusable pages in an ordered mapping whose
insertion order is their age, strands a take-back depth first from a stack, and carries the
reach of a page as a flag inherited when the page is made. This model is
one class over plain dicts: it derives the window edge arithmetically from the length and
releases the whole range that fell out, keeps the reusable pages in a heap of stamps with
lazy deletion, and strands a take-back breadth first from a queue. Where the contract forces
one answer - the lowest free page, the oldest release, the order pages are released in - both
must of course agree; everywhere else they were written to different shapes, so agreement
over a large generated population is evidence about the contract rather than about one
implementation of it.

The ten graded decisions this settles are listed in tests/test_outputs.py.
"""
import heapq


class Sim:
    def __init__(self):
        self.n = self.w = self.a = self.s = self.b = 0
        self.prev = {}
        self.body = {}
        self.fill = {}
        self.held = {}
        self.idx = {}
        self.kid = {}
        self.reach = {}
        self.free = []
        self.age = []
        self.stamp = {}
        self.clock = 0
        self.rq = {}
        self.wait = []
        self.on = []
        self.seq = 0
        self.out = []

    # --- the pool ----------------------------------------------------------------

    def sink(self):
        return -(-self.a // self.w)

    def take(self):
        """The lowest free page, or nothing at all."""
        if not self.free:
            return 0
        return heapq.heappop(self.free)

    def give(self, pid):
        """Straight back to the pool, wherever the page came from."""
        self.prev.pop(pid, None)
        self.body.pop(pid, None)
        self.fill.pop(pid, None)
        self.held.pop(pid, None)
        self.stamp.pop(pid, None)
        self.reach.pop(pid, None)
        heapq.heappush(self.free, pid)

    def strip(self, pid):
        """Out of the tree with everything below it, back to the pool where it can go."""
        gone = 0
        queue = [pid]
        while queue:
            here = queue.pop(0)
            queue.extend(self.kid.pop(here, []))
            self.unlist(here)
            if self.held.get(here, 0) == 0:
                self.give(here)
                gone += 1
            else:
                self.reach[here] = False
        return gone

    def oldest(self):
        """The reusable page released longest ago; the heap carries stale entries."""
        while self.age:
            when, pid = self.age[0]
            if self.stamp.get(pid) == when and self.held.get(pid, 0) == 0:
                return pid
            heapq.heappop(self.age)
        return 0

    def rest(self, pid):
        """One holder fewer. The last one leaving decides reusable against free."""
        left = self.held.get(pid, 0) - 1
        self.held[pid] = left
        if left > 0:
            return
        if self.fill.get(pid, 0) != self.w or not self.reach.get(pid):
            self.strip(pid)
            return
        self.clock += 1
        self.stamp[pid] = self.clock
        heapq.heappush(self.age, (self.clock, pid))

    def grip(self, pid):
        """One more holder. A reusable page stops being reusable."""
        if self.held.get(pid, 0) == 0:
            self.stamp.pop(pid, None)
        self.held[pid] = self.held.get(pid, 0) + 1

    def unlist(self, pid):
        key = (self.prev.get(pid, 0), self.body.get(pid))
        if self.idx.get(key) == pid:
            del self.idx[key]
        sib = self.kid.get(key[0])
        if sib is not None and pid in sib:
            sib.remove(pid)

    def back(self):
        """Take back the oldest release, with every page under it that is loose."""
        pid = self.oldest()
        if not pid:
            return 0
        self.stamp.pop(pid, None)
        self.out.append("gone %d %d" % (pid, self.strip(pid)))
        return pid

    def page(self):
        """The order of supply, one page at a time."""
        got = self.take()
        if got:
            return got
        if self.back():
            return self.take()
        return 0

    # --- residency ---------------------------------------------------------------

    def size(self, r):
        return r["fed"] + r["made"]

    def edge(self, r):
        """The lowest page outside the first tokens that residency still wants."""
        n = self.size(r)
        if n <= self.s:
            return self.sink()
        return max(self.sink(), (n - self.s) // self.w)

    def shed(self, r):
        """Release whatever the window has moved past, in token order."""
        want = self.edge(r)
        while r["at"] < want:
            pid = r["pg"].pop(r["at"], 0)
            if pid:
                self.rest(pid)
            r["at"] += 1

    def loose(self, r):
        for j in sorted(r["pg"]):
            self.rest(r["pg"][j])
        r["pg"] = {}

    # --- writing -----------------------------------------------------------------

    def write(self, r, tok):
        n = self.size(r)
        j, off = divmod(n, self.w)
        if off:
            pid = r["pg"][j]
        else:
            pid = self.page()
            if not pid:
                return False
            under = r["pg"][j - 1] if j else 0
            self.prev[pid] = under
            self.body[pid] = None
            self.fill[pid] = 0
            self.held[pid] = 1
            self.reach[pid] = under == 0 or bool(self.reach.get(under))
            self.kid.setdefault(under, []).append(pid)
            r["pg"][j] = pid
        buf = r["buf"].setdefault(pid, [])
        buf.append(tok)
        self.fill[pid] = off + 1
        if off + 1 == self.w:
            keep = tuple(buf)
            r["buf"].pop(pid)
            twin = self.idx.get((self.prev[pid], keep), 0)
            self.body[pid] = keep
            if twin:
                self.strip(pid)
                self.grip(twin)
                r["pg"][j] = twin
            elif self.reach.get(pid):
                self.idx[(self.prev[pid], keep)] = pid
        return True

    # --- the two phases ----------------------------------------------------------

    def walk(self, r):
        """As far from the start of the prompt as the pages still reach."""
        ask = r["ask"]
        prev = 0
        j = 0
        while (j + 1) * self.w <= len(ask):
            pid = self.idx.get((prev, tuple(ask[j * self.w:(j + 1) * self.w])), 0)
            if not pid:
                break
            self.grip(pid)
            r["pg"][j] = pid
            prev = pid
            j += 1
        return j

    def settle(self, r):
        self.shed(r)
        self.wait.remove(r["name"])
        self.on.append(r["name"])

    def feed(self, r, b):
        fresh = not r["got"]
        used = 0
        if fresh:
            used = self.walk(r) * self.w
            r["fed"] = used
            r["got"] = True
            r["at"] = self.sink()
        rest = len(r["ask"]) - r["fed"]
        if rest == 0:
            self.out.append("fill %s %d 0" % (r["name"], used))
            self.settle(r)
            return 0, True, True
        if rest <= b:
            want = rest
        else:
            want = (r["fed"] + b) // self.w * self.w - r["fed"]
        if want <= 0:
            if fresh:
                self.out.append("fill %s %d 0" % (r["name"], used))
            return 0, True, False
        put = 0
        while put < want:
            if not self.write(r, r["ask"][r["fed"]]):
                if fresh or put:
                    self.out.append("fill %s %d %d" % (r["name"], used, put))
                return 0, False, False
            r["fed"] += 1
            put += 1
        self.out.append("fill %s %d %d" % (r["name"], used, put))
        if r["fed"] == len(r["ask"]):
            self.settle(r)
        return put, True, True

    def stall(self, r):
        """Preemption: the newest resident request, or the one that asked."""
        who = self.rq[self.on[-1]] if self.on else r
        self.out.append("hold %s" % who["name"])
        self.loose(who)
        who["fed"] = 0
        who["made"] = 0
        who["got"] = False
        who["at"] = 0
        who["buf"] = {}
        if who["name"] in self.on:
            self.on.remove(who["name"])
        if who["name"] not in self.wait:
            spot = 0
            while spot < len(self.wait) and self.rq[self.wait[spot]]["seq"] < who["seq"]:
                spot += 1
            self.wait.insert(spot, who["name"])

    def step(self):
        b = self.b
        for name in self.on[:b]:
            r = self.rq.get(name)
            if r is None:
                continue
            if not self.write(r, r["out"][r["made"]]):
                self.stall(r)
                return
            r["made"] += 1
            b -= 1
            self.shed(r)
            if r["made"] == len(r["out"]):
                self.loose(r)
                self.on.remove(name)
                self.out.append("done %s" % name)
        while b > 0 and self.wait:
            r = self.rq[self.wait[0]]
            used, fine, more = self.feed(r, b)
            if not fine:
                self.stall(r)
                return
            if not more:
                return
            b -= used

    # --- the program ---------------------------------------------------------------

    def born(self, name, ask, out):
        self.seq += 1
        self.rq[name] = {
            "name": name, "seq": self.seq, "ask": ask, "out": out,
            "fed": 0, "made": 0, "pg": {}, "buf": {}, "got": False, "at": 0,
        }
        self.wait.append(name)

    def ex(self, f):
        op = f[0]
        if op == "pool":
            self.n, self.w, self.a, self.s, self.b = (int(x) for x in f[1:6])
            self.free = list(range(1, self.n + 1))
            heapq.heapify(self.free)
        elif op == "ask":
            self.born(f[1], spread(f[2]), spread(f[3]))
        elif op == "bulk":
            pre = spread(f[3])
            for i in range(int(f[2])):
                self.born(f[1] + str(i), pre + [1000 + i] * int(f[4]),
                          [2000 + i] * int(f[5]))
        elif op == "step":
            self.step()
        elif op == "stop":
            r = self.rq.pop(f[1], None)
            if r is not None:
                self.loose(r)
                if f[1] in self.on:
                    self.on.remove(f[1])
                if f[1] in self.wait:
                    self.wait.remove(f[1])
        elif op == "at":
            r = self.rq.get(f[1])
            i = int(f[2])
            pid = 0
            if r is not None and 0 <= i < self.size(r):
                pid = r["pg"].get(i // self.w, 0)
            self.out.append("at %s %d %s" % (f[1], i, pid if pid else "none"))


def spread(spec):
    if spec == "-":
        return []
    out = []
    for part in spec.split(","):
        cnt, _, val = part.partition(":")
        out.extend([int(val)] * int(cnt))
    return out


def expect(lines):
    sim = Sim()
    for line in lines:
        line = line.strip()
        if line:
            sim.ex(tuple(line.split()))
    return sim.out
