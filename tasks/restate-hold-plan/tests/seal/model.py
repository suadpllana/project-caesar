"""The sealed model of the recompute plan. Grading only; never reachable by submitted code.

It is written straight from the brief, recursively, and apart from the reference in
solution/, which settles iteratively in time order. The two agree on every enumerated
pipeline (gt.json was frozen from this file) and on every generated one.

Vocabulary, as the brief uses it:

  partition   (name, index). Hourly index h spans hours [h, h+1); daily index d spans
              [24d, 24d+24). A partition ends at the end of its span.
  reached     the corrected partition, and every partition of a step that has ended by now
              and whose declared reads include a reached partition - whether or not the
              partitions in between still exist.
  exists      ended by now, and either published or still inside its keep: now < end + keep.
  line        every reached partition of a step that exists gets exactly one line, a run or a
              hold; a partition that does not exist is computed for the plan (a temp line) only
              when a made line reads it.

Every rule below carries the number the trace (authoring/restate-hold-plan/trace.md) cites.
"""
import heapq
import sys

sys.setrecursionlimit(1000000)

H, D = "h", "d"


# --- R1  the pipeline file -------------------------------------------------------------

class Pipe:
    """now, the datasets in declaration order, their reads, roll-ups, publications, the fix."""

    def __init__(self, text):
        self.now = None
        self.names = []
        self.grain = {}
        self.keep = {}
        self.reads = {}          # a step's name -> [(kind, source, width)]; sources absent
        self.roll = {}           # an hourly name -> the daily roll-up that stands in for it
        self.pins = set()
        self.fix = None
        for raw in text.splitlines():
            ws = raw.split()
            if not ws:
                continue
            if ws[0] == "now":
                self.now = int(ws[1])
            elif ws[0] in ("src", "step"):
                name = ws[1]
                self.names.append(name)
                self.grain[name] = ws[2]
                self.keep[name] = int(ws[3])
                if ws[0] == "step":
                    self.reads[name] = [read_spec(tok) for tok in ws[4:]]
            elif ws[0] == "stand":
                self.roll[ws[2]] = ws[1]
            elif ws[0] == "pin":
                for part in ws[2:]:
                    self.pins.add((ws[1], int(part)))
            elif ws[0] == "fix":
                self.fix = (ws[1], int(ws[2]))
        self.pos = {name: k for k, name in enumerate(self.names)}


def read_spec(tok):
    """R2  the four reads: x (same), x/d (the hours of the day), x~w (window), x-1 (previous)."""
    if tok.endswith("/d"):
        return ("day", tok[:-2], 0)
    if tok.endswith("-1"):
        return ("prev", tok[:-2], 0)
    if "~" in tok:
        name, width = tok.split("~")
        return ("win", name, int(width))
    return ("same", tok, 0)


def span(pp, name, i):
    """R3  (start, end) of a partition in hours."""
    if pp.grain[name] == H:
        return i, i + 1
    return 24 * i, 24 * i + 24


def ends(pp, name, i):
    return span(pp, name, i)[1]


def declared(pp, name, i):
    """R2  what partition (name, i) reads, one group per read, before hour 0 dropped (R4)."""
    out = []
    for kind, src, width in pp.reads[name]:
        if kind == "same":
            parts = [i]
        elif kind == "day":
            parts = list(range(24 * i, 24 * i + 24))
        elif kind == "win":
            parts = list(range(i - width + 1, i + 1))
        else:
            # the latest partition of src that has ended by the time this one starts
            begin = span(pp, name, i)[0]
            parts = [begin - 1] if pp.grain[src] == H else [begin // 24 - 1]
        out.append((kind, src, [p for p in parts if p >= 0]))
    return out


class Plan:
    def __init__(self, pp):
        self.pp = pp
        self.memo = {}
        self.reached = self.reach()

    # --- R5  existence ------------------------------------------------------------------
    def ended(self, name, i):
        return i >= 0 and ends(self.pp, name, i) <= self.pp.now

    def exists(self, name, i):
        if not self.ended(name, i):
            return False
        if (name, i) in self.pp.pins:
            return True
        return self.pp.now < ends(self.pp, name, i) + self.pp.keep[name]

    # --- R6  what the correction reaches -------------------------------------------------
    def reach(self):
        """Walk forward from the fix. Every read looks back, so this starts at the fix."""
        pp = self.pp
        readers = {}
        for name in pp.names:
            for kind, src, width in pp.reads.get(name, ()):
                readers.setdefault(src, []).append((name, kind, width))
        seen = {pp.fix}
        todo = [pp.fix]
        while todo:
            src, i = todo.pop()
            for name, kind, width in readers.get(src, ()):
                for j in self.read_by(src, i, name, kind, width):
                    if self.ended(name, j) and (name, j) not in seen:
                        seen.add((name, j))
                        todo.append((name, j))
        return seen

    def read_by(self, src, i, name, kind, width):
        """The partitions of `name` whose `kind` read of `src` includes partition i."""
        pp = self.pp
        if kind == "same":
            return [i]
        if kind == "day":
            return [i // 24]
        if kind == "win":
            return list(range(i, i + width))
        if pp.grain[src] == pp.grain[name]:
            return [i + 1]
        if pp.grain[src] == D:                  # an hourly step reading the previous day
            return list(range(24 * (i + 1), 24 * (i + 1) + 24))
        return [(i + 1) // 24] if (i + 1) % 24 == 0 else []

    # --- R7  the flags of a stored partition ---------------------------------------------
    def stored(self, name, i):
        """(changed, agrees) of a partition that exists, once it has been settled."""
        pp = self.pp
        if (name, i) == pp.fix:
            return True, True                   # the correction itself
        if (name, i) not in self.reached or name not in pp.reads:
            return False, True                  # not reached: untouched and in agreement
        rec = self.settle(name, i)
        if rec["line"] == "run":
            return True, rec["agrees"]          # rerun: changed, agrees if its reads did
        return False, False                     # held: unchanged and no longer agreeing

    # --- R8  computing one partition: a run, or a temp ------------------------------------
    def settle(self, name, i):
        key = (name, i)
        if key in self.memo:
            return self.memo[key]
        pp = self.pp
        rec = {"ok": True, "changed": False, "agrees": True, "rolled": False,
               "after": [], "temps": []}
        here = self.exists(name, i)
        if here and key in pp.pins:
            rec["line"], rec["word"] = "hold", "pinned"      # R9  never rewritten
            self.memo[key] = rec
            return rec
        for kind, src, parts in declared(pp, name, i):
            if kind == "day" and self.stands_in(rec, name, src, i, parts):
                continue
            for part in parts:
                self.take(rec, src, part)
        if not here:
            rec["line"] = "temp" if rec["ok"] else "fail"
        elif not rec["ok"]:
            rec["line"], rec["word"] = "hold", "lost"        # R9  cannot be computed
        elif not rec["changed"]:
            rec["line"], rec["word"] = "hold", "same"        # R9  a rerun changes nothing
        else:
            rec["line"] = "run"                              # R10 the mode of a run
            if not rec["agrees"]:
                rec["word"] = "part"
            elif rec["rolled"]:
                rec["word"] = "sub"
            else:
                rec["word"] = "full"
        self.memo[key] = rec
        return rec

    def stands_in(self, rec, name, src, day, hours):
        """R11 a roll-up reads in place of a day of hours when one of them is missing."""
        pp = self.pp
        roll = pp.roll.get(src)
        if roll is None or roll == name:
            return False                        # never for the roll-up's own computation
        if all(self.exists(src, h) for h in hours):
            return False
        if not self.exists(roll, day):
            return False
        changed, agrees = self.stored(roll, day)
        if not agrees:
            return False                        # a roll-up stands in only while it agrees
        rec["rolled"] = True
        rec["changed"] |= changed
        if self.memo.get((roll, day), {}).get("line") == "run":
            rec["after"].append((roll, day))
        return True

    def take(self, rec, src, part):
        """R12 one read: stored if it exists, computed for the plan if not, never a source."""
        pp = self.pp
        if self.exists(src, part):
            changed, agrees = self.stored(src, part)
            rec["changed"] |= changed
            rec["agrees"] &= agrees
            if self.memo.get((src, part), {}).get("line") == "run":
                rec["after"].append((src, part))
            return
        if src not in pp.reads:
            rec["ok"] = False                   # an expired source partition is gone
            return
        sub = self.settle(src, part)
        if not sub["ok"]:
            rec["ok"] = False
            return
        rec["changed"] |= sub["changed"]
        rec["agrees"] &= sub["agrees"]
        rec["after"].append((src, part))
        rec["temps"].append((src, part))

    # --- R13 the plan: lines by demand, then the order --------------------------------------
    def plan(self):
        pp = self.pp
        key = lambda k: (ends(pp, k[0], k[1]), pp.pos[k[0]])
        lined = sorted((k for k in self.reached if k[0] in pp.reads and self.exists(*k)),
                       key=key)
        for k in lined:
            self.settle(*k)
        runs = [k for k in lined if self.memo[k]["line"] == "run"]
        holds = [k for k in lined if self.memo[k]["line"] == "hold"]

        # R13 a temp line for every partition a made line computed, and for nothing else
        made = set(runs)
        todo = list(runs)
        while todo:
            k = todo.pop()
            for t in self.memo[k]["temps"]:
                if t not in made:
                    made.add(t)
                    todo.append(t)

        # R14 each line after what it read; of the lines free to go, earliest end, then the
        # dataset declared first
        need = {k: set(self.memo[k]["after"]) & made for k in made}
        users = {}
        for k, before in need.items():
            for b in before:
                users.setdefault(b, []).append(k)
        free = [(key(k), k) for k in made if not need[k]]
        heapq.heapify(free)
        out = []
        while free:
            _, k = heapq.heappop(free)
            rec = self.memo[k]
            if rec["line"] == "run":
                out.append("run %s %d %s" % (k[0], k[1], rec["word"]))
            else:
                out.append("temp %s %d" % (k[0], k[1]))
            for u in users.get(k, ()):
                need[u].discard(k)
                if not need[u]:
                    heapq.heappush(free, (key(u), u))
        if len(out) != len(made):
            raise AssertionError("the plan's reads form a cycle")

        # R15 the holds come last, earliest end first, then the dataset declared first
        for k in holds:
            out.append("hold %s %d %s" % (k[0], k[1], self.memo[k]["word"]))
        return out


def expect(lines):
    """The plan for one pipeline, given as its list of lines or as one text."""
    text = lines if isinstance(lines, str) else "\n".join(lines) + "\n"
    return Plan(Pipe(text)).plan()
