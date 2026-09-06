"""A second implementation of the serving rules, written from the specification.

It shares no code with the tree the agent edits: blocks are addressed by a joined
string rather than a token tuple, the pool is three parallel maps rather than a
class of records, and the step is written as a straight line rather than as a
driver calling four policy hooks. Agreement between this and the reference over
several hundred generated traces is the evidence that the rules in the
instruction determine one timeline and not a family of them.

The rules, in the order the engine applies them:

  A step begins by taking in whatever arrived on it. The engine then decides,
  one at a time and in arrival order, which waiting requests will come in, and
  stops at the first one that will not; a request comes in only if, once that
  step's decoding is done, the pool can take everything it needs without a
  request being put out, and only if the tokens it must work through fit in what
  is left of the step's token allowance.

  Decoding happens next. Every request that was in the pool when the step began
  produces one token. A request whose part block is full needs a new one; if the
  pool cannot give it, the latest arrival is put out and the engine tries again.
  A block that fills is looked up by its own tokens under the tokens in front of
  it: if the pool already holds that block, the request takes it and gives its
  own back.

  Requests that have produced their last token then finish, and the requests
  chosen at the top of the step come in. A request coming in takes every block
  of what it holds, keeping the ones the pool still has, and starts working from
  the first token whose block the pool no longer has. If the pool has nothing in
  it once all of that is done and a request is waiting, the first one waiting
  comes in whatever it costs.

  A block nothing refers to keeps its contents and stays. It leaves only when the
  pool needs the slot, and then the block that has gone longest without being
  taken leaves first, the older one first where two were last taken on the same
  step.
"""


def read(text):
    cap = span = budget = 0
    ids = []
    at = {}
    toks = {}
    plen = {}
    for raw in text.splitlines():
        bits = raw.split()
        if not bits:
            continue
        if bits[0] == "pool":
            cap = int(bits[1])
        elif bits[0] == "block":
            span = int(bits[1])
        elif bits[0] == "batch":
            budget = int(bits[1])
        elif bits[0] == "req":
            ids.append(bits[1])
            at[bits[1]] = int(bits[2])
            toks[bits[1]] = []
            plen[bits[1]] = 0
        elif bits[0] == "prompt":
            toks[bits[1]] += [int(x) for x in bits[2:]]
            plen[bits[1]] = len(toks[bits[1]])
        elif bits[0] == "emit":
            toks[bits[1]] += [int(x) for x in bits[2:]]
    return cap, span, budget, ids, at, toks, plen


class Model(object):
    def __init__(self, text):
        (self.cap, self.span, self.budget, self.ids, self.at,
         self.toks, self.plen) = read(text)
        self.refs = {}
        self.touch = {}
        self.age = {}
        self.priv = 0
        self.clock = 0
        self.have = dict((i, 0) for i in self.ids)
        self.seen = dict((i, False) for i in self.ids)
        self.pos = dict((i, n) for n, i in enumerate(self.ids))
        self.inpool = []
        self.wait = []
        self.done = set()
        self.rows = []

    def tag(self, rid, j):
        return ",".join(str(x) for x in self.toks[rid][: (j + 1) * self.span])

    def tags(self, rid, upto):
        return [self.tag(rid, j) for j in range(upto // self.span)]

    def state(self):
        return (dict(self.refs), dict(self.touch), dict(self.age), self.priv,
                self.clock)

    def restore(self, snap):
        self.refs, self.touch, self.age, self.priv, self.clock = (
            dict(snap[0]), dict(snap[1]), dict(snap[2]), snap[3], snap[4])

    def busy(self):
        return len(self.refs) + self.priv

    def evict(self):
        loose = [k for k in self.refs if self.refs[k] == 0]
        if not loose:
            return False
        loose.sort(key=lambda k: (self.touch[k], self.age[k]))
        k = loose[0]
        del self.refs[k]
        del self.touch[k]
        del self.age[k]
        return True

    def grab(self, tag, t):
        if tag not in self.refs:
            while self.busy() >= self.cap:
                if not self.evict():
                    return False
            self.refs[tag] = 0
            self.age[tag] = self.clock
            self.clock += 1
        self.refs[tag] += 1
        self.touch[tag] = t
        return True

    def slot(self):
        while self.busy() >= self.cap:
            if not self.evict():
                return False
        self.priv += 1
        return True

    def let(self, rid, upto):
        for tag in self.tags(rid, upto):
            if self.refs.get(tag):
                self.refs[tag] -= 1
        if upto % self.span:
            self.priv -= 1

    def start(self, rid, tgt):
        n = 0
        for tag in self.tags(rid, tgt):
            if tag not in self.refs:
                break
            n += 1
        return n * self.span

    def target(self, rid):
        return self.plen[rid] if self.have[rid] == 0 else self.have[rid]

    def playable(self, run, joiners, t):
        snap = self.state()
        try:
            live = list(run)
            marks = dict((i, self.have[i]) for i in run)
            for rid in run:
                if rid not in live:
                    continue
                lost = False
                while marks[rid] % self.span == 0 and not self.slot():
                    if not live:
                        return False
                    victim = max(live, key=lambda i: self.pos[i])
                    self.let(victim, marks[victim])
                    live.remove(victim)
                    if victim == rid:
                        lost = True
                        break
                if lost:
                    continue
                marks[rid] += 1
                if marks[rid] % self.span == 0:
                    self.priv -= 1
                    if not self.grab(self.tag(rid, marks[rid] // self.span - 1), t):
                        return False
            for rid in list(live):
                if marks[rid] >= len(self.toks[rid]):
                    self.let(rid, marks[rid])
                    live.remove(rid)
            spend = 0
            for rid in joiners:
                tgt = self.target(rid)
                spend += tgt - self.start(rid, tgt)
                for tag in self.tags(rid, tgt):
                    if not self.grab(tag, t):
                        return False
                if tgt % self.span and not self.slot():
                    return False
            return spend
        finally:
            self.restore(snap)

    def bring(self, rid, t):
        tgt = self.target(rid)
        p = self.start(rid, tgt)
        for tag in self.tags(rid, tgt):
            while not self.grab(tag, t):
                if not self.inpool:
                    raise RuntimeError("no room on entry")
                self.oust(max(self.inpool, key=lambda i: self.pos[i]), t)
        if tgt % self.span:
            while not self.slot():
                if not self.inpool:
                    raise RuntimeError("no room for the tail")
                self.oust(max(self.inpool, key=lambda i: self.pos[i]), t)
        self.rows.append((self.pos[rid],
                          "resume" if self.seen[rid] else "admit", t, p))
        self.seen[rid] = True
        self.have[rid] = tgt
        self.inpool.append(rid)
        self.inpool.sort(key=lambda i: self.pos[i])

    def oust(self, rid, t):
        self.let(rid, self.have[rid])
        self.inpool.remove(rid)
        self.wait.append(rid)
        self.wait.sort(key=lambda i: self.pos[i])
        self.rows.append((self.pos[rid], "preempt", t, self.have[rid]))

    def stop(self, rid, t):
        self.let(rid, self.have[rid])
        self.inpool.remove(rid)
        self.done.add(rid)
        self.rows.append((self.pos[rid], "done", t))

    def turn(self, t):
        for rid in self.ids:
            if self.at[rid] == t:
                self.wait.append(rid)
        self.wait.sort(key=lambda i: self.pos[i])
        run = list(self.inpool)
        left = self.budget - len(run)
        joiners = []
        for rid in list(self.wait):
            spend = self.playable(run, joiners + [rid], t)
            if spend is False or spend > left:
                break
            joiners.append(rid)
            self.wait.remove(rid)
        for rid in run:
            if rid not in self.inpool:
                continue
            lost = False
            while self.have[rid] % self.span == 0 and not self.slot():
                if not self.inpool:
                    raise RuntimeError("nothing left to put out")
                victim = max(self.inpool, key=lambda i: self.pos[i])
                self.oust(victim, t)
                if victim == rid:
                    lost = True
                    break
            if lost:
                continue
            self.have[rid] += 1
            if self.have[rid] % self.span == 0:
                self.priv -= 1
                self.grab(self.tag(rid, self.have[rid] // self.span - 1), t)
        for rid in run:
            if rid in self.inpool and self.have[rid] >= len(self.toks[rid]):
                self.stop(rid, t)
        for rid in joiners:
            self.bring(rid, t)
        if not self.inpool and self.wait:
            head = self.wait.pop(0)
            self.bring(head, t)

    def play(self):
        total = sum(len(self.toks[i]) for i in self.ids)
        stop = 4 * total + 4 * len(self.ids) + 16
        t = 0
        while len(self.done) < len(self.ids):
            if t > stop:
                raise RuntimeError("the run did not settle")
            self.turn(t)
            t += 1
        return self.rows


def play(text):
    return Model(text).play()
