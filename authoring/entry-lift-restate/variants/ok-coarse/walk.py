"""The settle, reopening by name and by section rather than by slot.

An entry's lookups are remembered only as the names they asked for and the sections they
passed through. A write reopens every entry behind it that asked for that name anywhere; a
link reopens every entry behind it that passed through that section. That is a superset of
the entries a slot-exact index would reopen - more work, never less - and the entry that
found nothing where a mask stood is inside it, which is the part that has to hold.
"""
import heapq

from cf import book, sect, step, tell, wake


class Run:
    __slots__ = ("bk", "st", "key", "val", "names", "secs",
                 "byname", "bysec", "heap", "queued")

    def __init__(self, prog):
        self.bk = book.Book(prog)
        self.st = sect.Store()
        n = len(prog.ents)
        self.key = [None] * n
        self.val = [None] * n
        self.names = [frozenset()] * n
        self.secs = [frozenset()] * n
        self.byname = {}
        self.bysec = {}
        self.heap = []
        self.queued = set()

    def push(self, pos):
        if pos < self.bk.upto and pos not in self.queued:
            self.queued.add(pos)
            heapq.heappush(self.heap, pos)

    def push_name(self, name, pos):
        for other in self.byname.get(name, ()):
            if other > pos:
                self.push(other)

    def push_sec(self, sec, pos):
        for other in self.bysec.get(sec, ()):
            if other > pos:
                self.push(other)

    def note(self, i, names, secs):
        for held, index in ((self.names, self.byname), (self.secs, self.bysec)):
            was = held[i]
            fresh = names if index is self.byname else secs
            if was == fresh:
                continue
            for gone in was - fresh:
                index[gone].discard(i)
            for new in fresh - was:
                index.setdefault(new, set()).add(i)
            held[i] = frozenset(fresh)

    def redo(self, i):
        saw = (set(), set())
        if self.bk.active(i):
            sec = self.st.sec_before(i)
            key, val = step.plan(self.st, self.bk.ents[i], sec, i, saw)
        else:
            key, val = None, None
        self.note(i, saw[0], saw[1])

        if self.key[i] == key and self.val[i] == val:
            return
        was_key = self.key[i]
        self.key[i], self.val[i] = key, val
        if was_key == ("sec",) or key == ("sec",):
            self.move(i, key == ("sec",), val)
            return
        for entry, adding in ((was_key, False), (key, True)):
            if entry is None:
                continue
            if adding:
                self.st.put(entry, i, val)
            else:
                self.st.drop(entry, i)
            if entry[0] == "l":
                self.push_sec(entry[1], i)
            else:
                self.push_name(entry[2], i)

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
        while self.heap:
            pos = heapq.heappop(self.heap)
            self.queued.discard(pos)
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
        elif head in ("off", "back"):
            for i in run.bk.turn(stp[1], head == "off"):
                run.push(i)
        elif head == "get":
            passes = run.settle()
            tell.one(out, stp[1], stp[2],
                     sect.read(run.st, stp[1], stp[2], run.bk.upto, None), passes)
        else:
            passes = run.settle()
            held, masked, links = run.st.board()
            tell.board(out, held, masked, links, passes)
