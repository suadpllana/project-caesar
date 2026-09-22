"""The sealed resolver: what a program is supposed to print.

Written apart from the reference under `solution/`, and deliberately built on a different
structure, so that a program agreeing with both has satisfied the contract rather than an
implementation choice.

  - the board is three separate stores here (values, masks, links), each holding the ordered
    positions that wrote it, where the reference keeps one keyed store of tagged contents;
  - the climb is recursive and carries the sections it has visited as a list;
  - invalidation is by *name* and by *section* rather than by the exact slot key, which
    reopens a superset of the entries the reference reopens: coarser, still exact.

Both settle the same twelve decisions:

   1  a read takes the value in the slot, finds nothing if the slot is masked, and otherwise
      follows the section's link and looks again; a section reached twice ends the climb
   2  `add` reads through the climb and writes into the section the walk is carrying
   3  `add` does nothing when the read finds nothing
   4  `clr` leaves the climb free to go on where `cut` stops it
   5  every entry acts in the section the walk carries, which starts at 0 in every pass
   6  an entry whose `if` condition is not met does nothing at all, section entries included
   7  every settle starts from a clean board with every `once` entry asleep again
   8  between passes the lowest-numbered sleeping entry whose condition is met wakes, one per pass
   9  that condition is read in the section the finished pass gave its position, over that board
  10  a woken entry is applied on later passes without being tested again
  11  a lifted change takes no part in any pass and can never wake
  12  the printed format, the counts and the order of the detail lines

This file lives in a root-owned directory made 0700 before the submission runs, so code inside
the verifier cannot read it or compute its answers from it.
"""

import bisect
import heapq

ENTRY_ARGS = {"sec": 1, "set": 2, "clr": 1, "cut": 1, "add": 2, "lnk": 1}


class Row:
    __slots__ = ("kind", "a", "b", "guard", "g", "w", "chg")

    def __init__(self, kind, a, b, guard, g, w, chg):
        self.kind, self.a, self.b = kind, a, b
        self.guard, self.g, self.w = guard, g, w
        self.chg = chg


def read_program(lines):
    """A reader of this file's own, so nothing about parsing is shared with the reference."""
    rows, steps, nchg, held = [], [], 0, None
    for raw in lines:
        part = raw.split()
        if not part:
            continue
        head = part[0]
        if head == "open":
            held, nchg = nchg, nchg + 1
            continue
        if head == "shut":
            held = None
            continue
        if head in ("off", "back", "get", "all"):
            steps.append(tuple([head] + [int(x) for x in part[1:]]))
            continue
        guard = None
        g = w = 0
        if head in ("if", "once"):
            guard, g, w = head, int(part[1]), int(part[2])
            part = part[3:]
            head = part[0]
        args = [int(x) for x in part[1:1 + ENTRY_ARGS[head]]]
        if held is None:
            chg, nchg = nchg, nchg + 1
        else:
            chg = held
        rows.append(Row(head, args[0], args[1] if len(args) > 1 else 0, guard, g, w, chg))
        steps.append(("ent", len(rows) - 1))
    return rows, steps, nchg


# --- the board, kept as three stores of ordered writes -------------------------------

class Slots:
    """One store: key -> ascending write positions, and (key, position) -> what was written."""

    __slots__ = ("at", "was")

    def __init__(self):
        self.at = {}
        self.was = {}

    def add(self, key, pos, what):
        seq = self.at.get(key)
        if seq is None:
            seq = self.at[key] = []
        bisect.insort(seq, pos)
        self.was[(key, pos)] = what

    def cut(self, key, pos):
        seq = self.at[key]
        seq.pop(bisect.bisect_left(seq, pos))
        del self.was[(key, pos)]

    def upto(self, key, pos):
        seq = self.at.get(key)
        if not seq:
            return None
        i = bisect.bisect_left(seq, pos)
        return None if i == 0 else self.was[(key, seq[i - 1])]

    def last(self, key):
        seq = self.at.get(key)
        return self.was[(key, seq[-1])] if seq else None


class Sealed:
    def __init__(self, rows, nchg):
        self.rows = rows
        self.stood = 0
        self.gone = set()
        self.up = set()
        self.naps = []
        self.own = [[] for _ in range(nchg)]
        for i, row in enumerate(rows):
            self.own[row.chg].append(i)
        self.slot = Slots()                  # (sec, name) -> "v"/"e"/"m" with its number
        self.link = Slots()                  # sec -> the section it links to
        self.jump = []                       # ascending positions of firing `sec` entries
        self.jumpto = {}
        n = len(rows)
        self.wrote = [None] * n              # ("slot"|"link", key, what) or None
        self.saw_name = [()] * n
        self.saw_sec = [()] * n
        self.byname = {}
        self.bysec = {}
        self.queue = []
        self.waiting = set()

    # -- looking a name up, over the board as it stood before a position --------------

    def look(self, sec, name, pos, names, secs):
        return self._look(sec, name, pos, names, secs, [])

    def _look(self, sec, name, pos, names, secs, been):
        if sec in been:
            return None
        been.append(sec)
        if names is not None:
            names.add(name)
            secs.add(sec)
        what = self.slot.upto((sec, name), pos)
        if what is not None:
            if what[0] == "v":
                return what[1]
            if what[0] == "m":
                return None
        nxt = self.link.upto(sec, pos)
        if nxt is None:
            return None
        return self._look(nxt[1], name, pos, names, secs, been)

    def secat(self, pos):
        i = bisect.bisect_left(self.jump, pos)
        return 0 if i == 0 else self.jumpto[self.jump[i - 1]]

    # -- what one entry does ----------------------------------------------------------

    def awake(self, i):
        row = self.rows[i]
        if row.chg in self.gone:
            return False
        return row.guard != "once" or i in self.up

    def figure(self, i):
        names, secs = set(), set()
        if not self.awake(i):
            return None, names, secs
        row = self.rows[i]
        sec = self.secat(i)
        secs.add(sec)
        if row.guard == "if" and self.look(sec, row.g, i, names, secs) != row.w:
            return None, names, secs
        if row.kind == "sec":
            return ("jump", sec, row.a), names, secs
        if row.kind == "lnk":
            return ("link", sec, ("l", row.a)), names, secs
        names.add(row.a)
        if row.kind == "add":
            found = self.look(sec, row.a, i, names, secs)
            if found is None:
                return None, names, secs
            return ("slot", (sec, row.a), ("v", found + row.b)), names, secs
        mark = {"set": ("v", row.b), "clr": ("e",), "cut": ("m",)}[row.kind]
        return ("slot", (sec, row.a), mark), names, secs

    # -- reopening ---------------------------------------------------------------------

    def later(self, pos):
        if pos < self.stood and pos not in self.waiting:
            self.waiting.add(pos)
            heapq.heappush(self.queue, pos)

    def flag_name(self, name, after):
        for j in self.byname.get(name, ()):
            if j > after:
                self.later(j)

    def flag_sec(self, sec, after):
        for j in self.bysec.get(sec, ()):
            if j > after:
                self.later(j)

    def rework(self, i):
        made, names, secs = self.figure(i)
        for name in set(self.saw_name[i]) - names:
            self.byname[name].discard(i)
        for name in names - set(self.saw_name[i]):
            self.byname.setdefault(name, set()).add(i)
        for sec in set(self.saw_sec[i]) - secs:
            self.bysec[sec].discard(i)
        for sec in secs - set(self.saw_sec[i]):
            self.bysec.setdefault(sec, set()).add(i)
        self.saw_name[i], self.saw_sec[i] = frozenset(names), frozenset(secs)

        old = self.wrote[i]
        if old == made:
            return
        self.wrote[i] = made
        if (old is not None and old[0] == "jump") or (made is not None and made[0] == "jump"):
            self.shift(i, made)
            return
        for entry in (old, made):
            if entry is None:
                continue
            store = self.slot if entry[0] == "slot" else self.link
            if entry is old:
                store.cut(entry[1], i)
            else:
                store.add(entry[1], i, entry[2])
            if entry[0] == "slot":
                self.flag_name(entry[1][1], i)
            else:
                self.flag_sec(entry[1], i)

    def shift(self, i, made):
        """A `sec` entry started or stopped firing: every entry up to the next one moves."""
        idx = bisect.bisect_left(self.jump, i)
        here = idx < len(self.jump) and self.jump[idx] == i
        if made is not None:
            if not here:
                self.jump.insert(idx, i)
            self.jumpto[i] = made[2]
        elif here:
            self.jump.pop(idx)
            del self.jumpto[i]
        nxt = bisect.bisect_right(self.jump, i)
        end = self.jump[nxt] if nxt < len(self.jump) else self.stood - 1
        for pos in range(i + 1, end + 1):
            self.later(pos)

    def settle(self):
        for i in self.up:
            self.later(i)
        self.up.clear()
        passes = 1
        while True:
            while self.queue:
                i = heapq.heappop(self.queue)
                self.waiting.discard(i)
                self.rework(i)
            woke = None
            for i in self.naps:
                if i in self.up or self.rows[i].chg in self.gone:
                    continue
                row = self.rows[i]
                if self.look(self.secat(i), row.g, self.stood, None, None) == row.w:
                    woke = i
                    break
            if woke is None:
                return passes
            self.up.add(woke)
            self.later(woke)
            passes += 1

    def whole(self):
        held, masked = {}, []
        for key, seq in self.slot.at.items():
            if not seq:
                continue
            what = self.slot.was[(key, seq[-1])]
            if what[0] == "v":
                held[key] = what[1]
            elif what[0] == "m":
                masked.append(key)
        links = {}
        for sec, seq in self.link.at.items():
            if seq:
                links[sec] = self.link.was[(sec, seq[-1])][1]
        return held, sorted(masked), links


def expect(lines):
    rows, steps, nchg = read_program(lines)
    run = Sealed(rows, nchg)
    out = []
    for stp in steps:
        head = stp[0]
        if head == "ent":
            i = stp[1]
            run.stood = i + 1
            if rows[i].guard == "once":
                run.naps.append(i)
            run.later(i)
        elif head in ("off", "back"):
            chg = stp[1]
            want = head == "off"
            if (chg in run.gone) != want:
                if want:
                    run.gone.add(chg)
                else:
                    run.gone.discard(chg)
                for i in run.own[chg]:
                    run.later(i)
        elif head == "get":
            passes = run.settle()
            found = run.look(stp[1], stp[2], run.stood, None, None)
            out.append("get %d %d %s %d"
                       % (stp[1], stp[2], "-" if found is None else found, passes))
        else:
            passes = run.settle()
            held, masked, links = run.whole()
            out.append("all %d %d %d %d" % (passes, len(held), len(masked), len(links)))
            for key in sorted(held):
                out.append("v %d %d %d" % (key[0], key[1], held[key]))
            for key in masked:
                out.append("m %d %d" % key)
            for sec in sorted(links):
                out.append("l %d %d" % (sec, links[sec]))
    return out
