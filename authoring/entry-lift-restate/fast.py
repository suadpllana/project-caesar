"""The same rules, worked out again only where the journal moved.

A pass is a fold along the journal, so the board ahead of an entry cannot depend on anything
behind it. That gives two structures. Every slot and every link keeps the ordered list of the
positions that wrote it, so the board as of any position is one binary search away and the
board at the end is the last element. And every entry keeps the trail its climb walked - the
slots it looked at and passed over as well as the one it took a value from, and every link it
followed - indexed the other way round, so a withdrawal reopens exactly the entries whose
lookup can have moved.

Written to be the reference. `naive.py` is the specification it is checked against.
"""

import bisect
import heapq

from naive import Bad, parse  # the reader is frozen and not graded


class Fast:
    def __init__(self, ents, nchg):
        self.ents = ents
        self.upto = 0
        self.dead = set()
        self.woken = set()
        self.sleepers = []                       # positions of `once` entries, ascending
        self.by_chg = [[] for _ in range(nchg)]
        for i, ent in enumerate(ents):
            self.by_chg[ent.chg].append(i)
        n = len(ents)
        self.fired = [False] * n
        self.wkey = [None] * n
        self.wval = [None] * n
        self.trail = [frozenset()] * n
        self.wpos = {}                           # key -> ascending positions that write it
        self.wcon = {}                           # (key, pos) -> content
        self.dep = {}                            # key -> set of positions that consulted it
        self.secpos = []                         # ascending positions of firing `sec` entries
        self.secto = {}                          # position -> section it moves to
        self.heap = []
        self.queued = set()

    # -- the board as of a position -------------------------------------------------

    def _before(self, key, pos):
        """The content written to `key` by the last entry before `pos`, or None."""
        seq = self.wpos.get(key)
        if not seq:
            return None
        idx = bisect.bisect_left(seq, pos)
        if idx == 0:
            return None
        return self.wcon[(key, seq[idx - 1])]

    def _sec_before(self, pos):
        idx = bisect.bisect_left(self.secpos, pos)
        return 0 if idx == 0 else self.secto[self.secpos[idx - 1]]

    def _read(self, sec, name, pos, trail):
        """Climb from `sec` looking for `name`, over the board as it stood before `pos`."""
        seen = set()
        cur = sec
        while True:
            if cur in seen:
                return None
            seen.add(cur)
            key = ("s", cur, name)
            if trail is not None:
                trail.add(key)
            con = self._before(key, pos)
            if con is not None:
                if con[0] == "v":
                    return con[1]
                if con[0] == "m":
                    return None
            lkey = ("l", cur)
            if trail is not None:
                trail.add(lkey)
            lcon = self._before(lkey, pos)
            if lcon is None:
                return None
            cur = lcon[1]

    # -- the worklist ---------------------------------------------------------------

    def _push(self, pos):
        if pos < self.upto and pos not in self.queued:
            self.queued.add(pos)
            heapq.heappush(self.heap, pos)

    def _push_after(self, key, pos):
        for other in self.dep.get(key, ()):  # only entries behind it can have moved
            if other > pos:
                self._push(other)

    def _push_range(self, lo, hi):
        for pos in range(lo, hi + 1):
            self._push(pos)

    # -- evaluating one entry -------------------------------------------------------

    def _active(self, i):
        ent = self.ents[i]
        if ent.chg in self.dead:
            return False
        return ent.guard != "once" or i in self.woken

    def _plan(self, i):
        """What entry `i` does, and every key its lookups consulted, as the journal stands."""
        trail = set()
        if not self._active(i):
            return False, None, None, trail
        ent = self.ents[i]
        sec = self._sec_before(i)
        if ent.guard == "if" and self._read(sec, ent.g, i, trail) != ent.w:
            return False, None, None, trail
        kind = ent.kind
        if kind == "sec":
            return True, ("sec",), ent.a, trail
        if kind == "lnk":
            return True, ("l", sec), ("l", ent.a), trail
        if kind == "add":
            found = self._read(sec, ent.a, i, trail)
            if found is None:
                return True, None, None, trail
            return True, ("s", sec, ent.a), ("v", found + ent.b), trail
        key = ("s", sec, ent.a)
        if kind == "set":
            return True, key, ("v", ent.b), trail
        if kind == "clr":
            return True, key, ("e",), trail
        return True, key, ("m",), trail          # cut

    def _settle_one(self, i):
        fired, key, val, trail = self._plan(i)
        old_key, old_val = self.wkey[i], self.wval[i]

        for gone in self.trail[i] - trail:
            self.dep[gone].discard(i)
        for fresh in trail - self.trail[i]:
            self.dep.setdefault(fresh, set()).add(i)
        self.trail[i] = frozenset(trail)
        self.fired[i] = fired

        if old_key == key and old_val == val:
            return
        self.wkey[i], self.wval[i] = key, val

        if old_key == ("sec",) or key == ("sec",):
            self._move_section(i, key == ("sec",), val)
            return
        if old_key is not None:
            seq = self.wpos[old_key]
            seq.pop(bisect.bisect_left(seq, i))
            del self.wcon[(old_key, i)]
            self._push_after(old_key, i)
        if key is not None:
            seq = self.wpos.setdefault(key, [])
            bisect.insort(seq, i)
            self.wcon[(key, i)] = val
            self._push_after(key, i)

    def _move_section(self, i, now, target):
        """A `sec` entry started or stopped firing, or moved somewhere else.

        Every entry from here to the next firing `sec` entry works in a different section
        now, so each of them has to be looked at again - guards, targets and all.
        """
        idx = bisect.bisect_left(self.secpos, i)
        here = idx < len(self.secpos) and self.secpos[idx] == i
        if now:
            if not here:
                self.secpos.insert(idx, i)
            self.secto[i] = target
        elif here:
            self.secpos.pop(idx)
            del self.secto[i]
        nxt = bisect.bisect_right(self.secpos, i)
        end = self.secpos[nxt] if nxt < len(self.secpos) else self.upto - 1
        self._push_range(i + 1, end)

    def _drain(self):
        while self.heap:
            pos = heapq.heappop(self.heap)
            self.queued.discard(pos)
            self._settle_one(pos)

    # -- the settle -----------------------------------------------------------------

    def settle(self):
        for i in self.woken:
            self._push(i)
        self.woken.clear()
        passes = 1
        while True:
            self._drain()
            woke = None
            for i in self.sleepers:
                if i in self.woken or self.ents[i].chg in self.dead:
                    continue
                ent = self.ents[i]
                if self._read(self._sec_before(i), ent.g, self.upto, None) == ent.w:
                    woke = i
                    break
            if woke is None:
                return passes
            self.woken.add(woke)
            self._push(woke)
            passes += 1

    # -- the journal ----------------------------------------------------------------

    def append(self, i):
        self.upto = i + 1
        if self.ents[i].guard == "once":
            self.sleepers.append(i)
        self._push(i)

    def lift(self, chg, dead):
        if (chg in self.dead) == dead:
            return
        if dead:
            self.dead.add(chg)
        else:
            self.dead.discard(chg)
        for i in self.by_chg[chg]:
            self._push(i)

    # -- answering ------------------------------------------------------------------

    def read_end(self, sec, name):
        return self._read(sec, name, self.upto, None)

    def board(self):
        held, masked, links = {}, [], {}
        for key, seq in self.wpos.items():
            if not seq:
                continue
            con = self.wcon[(key, seq[-1])]
            if key[0] == "l":
                links[key[1]] = con[1]
            elif con[0] == "v":
                held[(key[1], key[2])] = con[1]
            elif con[0] == "m":
                masked.append((key[1], key[2]))
        return held, sorted(masked), links


def run(text):
    ents, steps, nchg = parse(text)
    eng = Fast(ents, nchg)
    out = []
    for step in steps:
        head = step[0]
        if head == "ent":
            eng.append(step[1])
        elif head == "off":
            eng.lift(step[1], True)
        elif head == "back":
            eng.lift(step[1], False)
        elif head == "get":
            passes = eng.settle()
            found = eng.read_end(step[1], step[2])
            out.append("get %d %d %s %d" % (step[1], step[2],
                                            "-" if found is None else found, passes))
        elif head == "all":
            passes = eng.settle()
            held, masked, links = eng.board()
            out.append("all %d %d %d %d" % (passes, len(held), len(masked), len(links)))
            for key in sorted(held):
                out.append("v %d %d %d" % (key[0], key[1], held[key]))
            for key in masked:
                out.append("m %d %d" % key)
            for sec in sorted(links):
                out.append("l %d %d" % (sec, links[sec]))
    return out


__all__ = ["Bad", "run"]
