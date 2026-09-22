import heapq

from cf import book, sect, step, tell, wake


class Run:
    __slots__ = ("bk", "st", "key", "val", "trail", "dep", "heap", "queued")

    def __init__(self, prog):
        self.bk = book.Book(prog)
        self.st = sect.Store()
        n = len(prog.ents)
        self.key = [None] * n
        self.val = [None] * n
        self.trail = [frozenset()] * n
        self.dep = {}
        self.heap = []
        self.queued = set()

    def push(self, pos):
        if pos < self.bk.upto and pos not in self.queued:
            self.queued.add(pos)
            heapq.heappush(self.heap, pos)

    def push_readers(self, key, pos):
        for other in self.dep.get(key, ()):
            if other > pos:
                self.push(other)

    def plan(self, i):
        trail = set()
        if not self.bk.active(i):
            return None, None, trail
        sec = self.st.sec_before(i)
        key, val = step.plan(self.st, self.bk.ents[i], sec, i, trail)
        return key, val, trail

    def redo(self, i):
        key, val, trail = self.plan(i)
        for gone in self.trail[i] - trail:
            self.dep[gone].discard(i)
        for fresh in trail - self.trail[i]:
            self.dep.setdefault(fresh, set()).add(i)
        self.trail[i] = frozenset(trail)

        was_key, was_val = self.key[i], self.val[i]
        if was_key == key and was_val == val:
            return
        self.key[i], self.val[i] = key, val
        if was_key == ("sec",) or key == ("sec",):
            self.move(i, key == ("sec",), val)
            return
        if was_key is not None:
            self.st.drop(was_key, i)
            self.push_readers(was_key, i)
        if key is not None:
            self.st.put(key, i, val)
            self.push_readers(key, i)

    def move(self, i, now, target):
        if now:
            self.st.sec_put(i, target)
        else:
            self.st.sec_drop(i)
        end = self.st.next_sec(i)
        if end is None:
            end = self.bk.upto - 1
        for pos in range(i + 1, end + 1):
            self.push(pos)

    def drain(self):
        heap, queued = self.heap, self.queued
        while heap:
            pos = heapq.heappop(heap)
            queued.discard(pos)
            self.redo(pos)

    def settle(self):
        for i in self.bk.woken:
            self.push(i)
        self.bk.woken.clear()
        passes = 1
        while True:
            self.drain()
            up = wake.next_up(self.st, self.bk)
            if up is None:
                return passes
            self.bk.woken.add(up)
            self.push(up)
            passes += 1


def play(prog, out):
    run = Run(prog)
    for stp in prog.steps:
        head = stp[0]
        if head == "ent":
            run.bk.append(stp[1])
            run.push(stp[1])
        elif head == "off" or head == "back":
            for i in run.bk.turn(stp[1], head == "off"):
                run.push(i)
        elif head == "get":
            passes = run.settle()
            found = sect.read(run.st, stp[1], stp[2], run.bk.upto, None)
            tell.one(out, stp[1], stp[2], found, passes)
        else:
            passes = run.settle()
            held, masked, links = run.st.board()
            tell.board(out, held, masked, links, passes)
