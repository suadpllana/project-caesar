"""The settle, driven from a sorted list of the entries that have to be looked at again.

The entries whose lookup consulted a key are kept as an ordered list per key rather than as a
set, so the ones behind a change are found by a binary search instead of by filtering the
whole set; and the list of entries waiting to be worked out again is kept in order and taken
from the front, which is what the fold needs.
"""
import bisect

from cf import book, sect, step, tell, wake


class Run:
    __slots__ = ("bk", "st", "key", "val", "trail", "dep", "waiting")

    def __init__(self, prog):
        self.bk = book.Book(prog)
        self.st = sect.Store()
        n = len(prog.ents)
        self.key = [None] * n
        self.val = [None] * n
        self.trail = [frozenset()] * n
        self.dep = {}
        self.waiting = []

    def push(self, pos):
        if pos >= self.bk.upto:
            return
        i = bisect.bisect_left(self.waiting, pos)
        if i == len(self.waiting) or self.waiting[i] != pos:
            self.waiting.insert(i, pos)

    def push_readers(self, key, pos):
        seq = self.dep.get(key)
        if not seq:
            return
        for other in seq[bisect.bisect_right(seq, pos):]:
            self.push(other)

    def redo(self, i):
        trail = set()
        if self.bk.active(i):
            sec = self.st.sec_before(i)
            key, val = step.plan(self.st, self.bk.ents[i], sec, i, trail)
        else:
            key, val = None, None

        old = self.trail[i]
        if old != trail:
            for gone in old - trail:
                seq = self.dep[gone]
                seq.pop(bisect.bisect_left(seq, i))
            for fresh in trail - old:
                seq = self.dep.get(fresh)
                if seq is None:
                    seq = self.dep[fresh] = []
                bisect.insort(seq, i)
            self.trail[i] = frozenset(trail)

        if self.key[i] == key and self.val[i] == val:
            return
        was_key, was_val = self.key[i], self.val[i]
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
        del was_val

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
        while self.waiting:
            self.redo(self.waiting.pop(0))

    def settle(self):
        for i in sorted(self.bk.woken):
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
