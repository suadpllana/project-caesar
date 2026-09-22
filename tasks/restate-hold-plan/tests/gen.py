"""Pipelines generated from a seed drawn after the agent has finished.

Twelve families. Ten are small and each is shaped around the rules it has to exercise, because
an unshaped population barely moves the readings this task exists to punish (measured while
designing it: a random pipeline put a roll-up in place of a day's hours in 73 of 95,000 lines).
Two are large and exist for the stated execution limit.

  plain    nothing reached has expired and nothing is published: every line is a full rerun
  reach    corrections behind an hourly layer that has expired, reaching kept daily roll-ups
  pins     published partitions the correction reaches, and what their readers do
  stand    a roll-up that may stand in for a day with a missing hour, published or not,
           declared before or after the step that reads the hours - the late case
  chain    steps that read their own previous partition, with published checkpoints
  window   trailing windows reaching expired partitions the correction never reached
  edge     corrections near hour 0 and keeps whose boundary falls inside a window or a day
  lost     sources whose keep has run out under a window, and holds that race for a reason
  cross    previous-period reads between grains, both ways
  mixed    any of the shapes above, with more steps around it
  long     three years of hourly history read through thirty-day hourly windows  (large)
  deep     a long chain of expired hourly partitions read through wide windows   (large)

Every pipeline is checked against the rules the brief states for a pipeline file before it is
used, and one whose plan would be empty is drawn again.
"""
import random

FAMILIES = [("plain", False), ("reach", False), ("pins", False), ("stand", False),
            ("chain", False), ("window", False), ("edge", False), ("lost", False),
            ("cross", False), ("mixed", False), ("long", True), ("deep", True)]
BIG_EACH = 4

NAMES = ["ev", "ck", "vw", "ses", "ord", "pay", "inv", "shp", "ret", "bal", "tot", "rol",
         "act", "use", "cst", "rat", "mix", "net", "fee", "tax", "adj", "gap", "lag", "cap",
         "vol", "hit", "bid", "ask", "fil", "rev", "dsh", "wk", "qty", "sku", "lot", "bin"]


class Build:
    """A pipeline under construction, in declaration order."""

    def __init__(self, rng, now):
        self.rng = rng
        self.now = now
        self.pool = rng.sample(NAMES, len(NAMES))
        self.rows = []           # [name, grain, keep, reads or None]
        self.rolls = []          # (roll-up, hourly)
        self.pins = {}
        self.fix = None

    def src(self, grain, keep):
        name = self.pool.pop()
        self.rows.append([name, grain, keep, None])
        return name

    def step(self, grain, keep, reads):
        name = self.pool.pop()
        self.rows.append([name, grain, keep, [r.replace("@", name) for r in reads]])
        return name

    def grain(self, name):
        return next(r[1] for r in self.rows if r[0] == name)

    def keep(self, name):
        return next(r[2] for r in self.rows if r[0] == name)

    def pin(self, name, part):
        """Publish a partition, if it has ended by now; only a step's partitions are published."""
        end = part + 1 if self.grain(name) == "h" else 24 * part + 24
        if part >= 0 and end <= self.now:
            self.pins.setdefault(name, set()).add(part)

    def exists_range(self, name):
        """The first and last partition of `name` that exist when nothing is published."""
        keep = self.keep(name)
        if self.grain(name) == "h":
            return max(0, self.now - keep), self.now - 1
        return max(0, (self.now - keep - 24) // 24 + 1), self.now // 24 - 1

    def correct(self, name, part):
        """Correct a source partition, moved inside the range where it still exists."""
        lo, hi = self.exists_range(name)
        self.fix = (name, min(max(part, lo), hi))

    def lines(self):
        out = ["now %d" % self.now]
        for name, grain, keep, reads in self.rows:
            if reads is None:
                out.append("src %s %s %d" % (name, grain, keep))
            else:
                out.append("step %s %s %d %s" % (name, grain, keep, " ".join(reads)))
        for roll, hourly in self.rolls:
            out.append("stand %s %s" % (roll, hourly))
        order = [r[0] for r in self.rows]
        for name in sorted(self.pins, key=order.index):
            out.append("pin %s %s" % (name, " ".join(str(p) for p in sorted(self.pins[name]))))
        out.append("fix %s %d" % self.fix)
        return out


def around(b, k):
    """A few more steps over what is declared already, so the motif is never alone."""
    rng = b.rng
    for _ in range(k):
        src = rng.choice([r[0] for r in b.rows])
        sg = b.grain(src)
        grain = rng.choice("hd")
        if grain == "h":
            if sg == "h":
                tok = src if rng.random() < 0.6 else "%s~%d" % (src, rng.randint(2, 12))
            else:
                tok = src + "-1"
        elif sg == "h":
            tok = src + "/d" if rng.random() < 0.7 else src + "-1"
        else:
            tok = rng.choice([src, "%s~%d" % (src, rng.randint(2, 6)), src + "-1"])
        reads = [tok]
        if rng.random() < 0.2:
            reads.append("@-1")
        keep = rng.choice([24, 48, 96, 240, 480, 1440]) if grain == "d" else \
            rng.choice([12, 24, 48, 96, 240, 1440])
        b.step(grain, keep, reads)


def hour_in(rng, day):
    return rng.randint(24 * day, 24 * day + 23)


def f_plain(rng):
    b = Build(rng, 24 * rng.randint(6, 14) + rng.choice([0, 5, 13]))
    raw = b.src("h", 1440)
    x = b.step("h", 1440, [raw])
    d = b.step("d", 1440, [x + "/d"])
    b.step("d", 1440, ["%s~%d" % (d, rng.randint(2, 4))])
    b.step("h", 1440, ["%s~%d" % (x, rng.randint(2, 6)), d + "-1"])
    if rng.random() < 0.5:
        b.step("d", 1440, [d, "@-1"])
    around(b, rng.randint(0, 2))
    for row in b.rows:
        row[2] = max(row[2], 1440)
    b.correct(raw, rng.randint(max(0, b.now - 72), b.now - 1))
    return b


def f_reach(rng):
    now = 24 * rng.randint(8, 16) + rng.choice([0, rng.randint(1, 23)])
    b = Build(rng, now)
    raw = b.src("h", 960)
    x = b.step("h", rng.choice([12, 24, 36, 48]), [raw])
    y = b.step("h", rng.choice([24, 48]), [x] if rng.random() < 0.5 else ["%s~%d" % (x, rng.randint(2, 6))])
    d = b.step("d", rng.choice([240, 480]), [y + "/d"])
    b.step("d", rng.choice([240, 480]), ["%s~%d" % (d, rng.randint(2, 5))])
    if rng.random() < 0.5:
        b.step("h", rng.choice([24, 96]), [d + "-1", x])
    around(b, rng.randint(0, 2))
    top = now // 24 - 1
    b.correct(raw, hour_in(rng, rng.randint(max(0, top - 7), max(0, top - 2))))
    return b


def f_pins(rng):
    now = 24 * rng.randint(8, 16) + rng.choice([0, rng.randint(1, 23)])
    b = Build(rng, now)
    raw = b.src("h" if rng.random() < 0.7 else "d", 960)
    rg = b.grain(raw)
    scene = rng.choice(["window", "window", "behind", "unreached"])
    a = b.step("d", rng.choice([96, 240, 480]), [raw + "/d" if rg == "h" else raw])
    p = b.step("d", rng.choice([240, 480]), [a])
    b.step("d", rng.choice([240, 480]), ["%s~%d" % (p, rng.randint(2, 4)), a])
    if scene == "behind":
        # a step reached only through the published partition, read beside a changed one
        mid = b.step("d", rng.choice([240, 480]), [p] if rng.random() < 0.7 else [p + "~2"])
        b.step("d", rng.choice([240, 480]), [mid, a] if rng.random() < 0.6 else [mid + "~2", a])
    if rng.random() < 0.4:
        b.step("h", rng.choice([48, 96]), [p + "-1", a + "-1"])
    around(b, rng.randint(0, 2))
    top = now // 24 - 1
    fd = rng.randint(max(0, top - 5), top)
    b.correct(raw, hour_in(rng, fd) if rg == "h" else fd)
    fd = b.fix[1] // 24 if rg == "h" else b.fix[1]
    if scene == "unreached":
        b.pin(p, fd - rng.randint(1, 3))
        b.pin(a, fd - rng.randint(1, 2))
    else:
        b.pin(p, fd)
        if rng.random() < 0.3:
            b.pin(a, fd + 1)
    return b


def f_stand(rng):
    """The late case: a roll-up that may stand in for a day of hours with one missing."""
    now = 24 * rng.randint(9, 16) + rng.choice([0, 0, rng.randint(1, 23)])
    b = Build(rng, now)
    raw = b.src("h", 960 if rng.random() < 0.85 else rng.choice([72, 96]))
    scene = rng.choice(["refuse", "use", "part", "order", "edge", "rollpart"])
    xkeep = rng.choice([12, 20, 24, 30, 36, 48, 60])
    x = b.step("h", xkeep, [raw + "~2"] if scene == "rollpart" else [raw])
    y = b.step("d", 480, [raw + "/d"]) if scene == "part" or rng.random() < 0.25 else None
    s_reads = [x + "/d"]
    if rng.random() < 0.5:
        s_reads.append("@-1")
    if y is not None:
        s_reads.append("%s~%d" % (y, rng.randint(2, 3)))
    skeep = rng.choice([48, 72, 240, 480, 480])
    if scene == "order" or rng.random() < 0.35:
        s = b.step("d", skeep, s_reads)
        if scene == "order":
            b.step("d", rng.choice([240, 480]), [raw + "/d"])
        r = b.step("d", rng.choice([240, 480]), [x + "/d"])
    else:
        r = b.step("d", rng.choice([240, 480]), [x + "/d"])
        s = b.step("d", skeep, s_reads)
    b.rolls.append((r, x))
    t = b.step("d", rng.choice([240, 480]), [r])
    b.step("d", rng.choice([240, 480]),
           ["%s~%d" % (s, rng.randint(2, 5)), "%s~%d" % (t, rng.randint(2, 4))])
    if rng.random() < 0.3:
        b.step("h", rng.choice([24, 48, 96]), [r + "-1", x])
    around(b, rng.randint(0, 1))
    lo = now - xkeep                      # the first hour of x that still exists
    top = now // 24 - 1
    if scene == "edge" and lo % 24:
        fd = lo // 24                     # the day the keep boundary cuts through
    else:
        fd = rng.randint(max(0, lo // 24 - 4), max(0, min(top, lo // 24 - 1)))
    if scene == "rollpart":
        b.correct(raw, rng.randint(24 * fd, 24 * fd + 22))
    else:
        b.correct(raw, hour_in(rng, fd))
    fh = b.fix[1]
    fd = fh // 24
    if scene == "refuse":
        b.pin(r, fd)
    elif scene == "part":
        b.pin(y, fd)
    elif scene == "rollpart":
        b.pin(x, fh + 1)
    elif rng.random() < 0.3:
        b.pin(r, fd + rng.randint(1, 2))
    if rng.random() < 0.2:
        b.pin(t, fd + rng.randint(0, 2))
    return b


def f_chain(rng):
    now = 24 * rng.randint(8, 20) + rng.choice([0, rng.randint(1, 23)])
    b = Build(rng, now)
    raw = b.src("h", 1440)
    daily = rng.random() < 0.6
    if daily:
        a = b.step("d", rng.choice([48, 96, 168]), [raw + "/d", "@-1"])
    else:
        a = b.step("h", rng.choice([12, 24, 48]), [raw, "@-1"])
    c = b.step("d", rng.choice([96, 240, 480]), [a + ("~3" if daily else "/d")])
    b.step("d", rng.choice([96, 240]), [c, "@-1"] if rng.random() < 0.5 else [c + "~2"])
    around(b, rng.randint(0, 2))
    fh = rng.randint(max(0, now - 144), now - 1)
    b.correct(raw, fh)
    fh = b.fix[1]
    fp = fh // 24 if daily else fh
    top = now // 24 - 1 if daily else now - 1
    if rng.random() < 0.7:
        b.pin(a, rng.randint(max(0, fp - (3 if daily else 60)), max(0, fp - 1)))
    if rng.random() < 0.5:
        b.pin(a, rng.randint(min(fp, top), top))
    return b


def f_window(rng):
    now = 24 * rng.randint(8, 16) + rng.choice([0, rng.randint(1, 23)])
    b = Build(rng, now)
    raw = b.src("d" if rng.random() < 0.5 else "h",
                960 if rng.random() < 0.7 else rng.choice([72, 120, 168]))
    rg = b.grain(raw)
    scene = rng.choice(["reach", "reach", "held"])
    a = b.step("d", rng.choice([48, 72, 96, 120]), [raw if rg == "d" else raw + "/d"])
    p = b.step("d", rng.choice([240, 480]), [a])
    if scene == "held":
        # reached only through a published partition, while its window reaches days that
        # expired and were never reached
        other = b.src("d", 960)
        c = b.step("d", rng.choice([48, 72]), [other])
        q = b.step("d", rng.choice([240, 480]),
                   ["%s~%d" % (p, rng.randint(1, 3) + 1), "%s~%d" % (c, rng.randint(3, 6))])
    else:
        q = b.step("d", rng.choice([240, 480]),
                   ["%s~%d" % (p, rng.randint(2, 4)), "%s~%d" % (a, rng.randint(3, 7))])
    b.step("d", rng.choice([240, 480]), ["%s~%d" % (q, rng.randint(2, 3))])
    around(b, rng.randint(0, 2))
    top = now // 24 - 1
    fd = rng.randint(max(0, top - 6), top)
    b.correct(raw, fd if rg == "d" else hour_in(rng, fd))
    fd = b.fix[1] if rg == "d" else b.fix[1] // 24
    if scene == "held" or rng.random() < 0.7:
        b.pin(p, fd)
    if rng.random() < 0.3:
        b.pin(a, fd + 1)
    return b


def f_edge(rng):
    now = 24 * rng.randint(3, 8) + rng.choice([0, rng.randint(1, 23)])
    b = Build(rng, now)
    raw = b.src("h", now + 24)
    x = b.step("h", rng.choice([6, 12, 18, 24, 30]), [raw])
    d = b.step("d", rng.choice([24, 48, 72]),
               [x + "/d", "@-1"] if rng.random() < 0.4 else [x + "/d"])
    b.step("d", rng.choice([48, 96]), ["%s~%d" % (d, rng.randint(2, 7))])
    b.step("h", rng.choice([12, 24, 48]), ["%s~%d" % (x, rng.randint(2, 10)), d + "-1"])
    if rng.random() < 0.5:
        r = b.step("d", rng.choice([48, 96, 240]), [x + "/d"])
        b.rolls.append((r, x))
    around(b, rng.randint(0, 2))
    b.correct(raw, rng.randint(0, min(now - 1, 40)))
    return b


def f_lost(rng):
    now = 24 * rng.randint(8, 16) + rng.choice([0, rng.randint(1, 23)])
    b = Build(rng, now)
    raw = b.src("h", rng.choice([96, 120, 168]))
    other = b.src("h", rng.choice([48, 72, 72, 960]))
    x = b.step("h", rng.choice([12, 24, 48]), [raw])
    d = b.step("d", rng.choice([240, 480]), [x + "/d"])
    p = b.step("d", rng.choice([240, 480]), [d])
    b.step("d", rng.choice([240, 480]), ["%s~%d" % (p, rng.randint(2, 5)), other + "/d"])
    b.step("h", rng.choice([24, 96]), ["%s~%d" % (other, rng.randint(12, 60)), x])
    if rng.random() < 0.4:
        r = b.step("d", rng.choice([240, 480]), [other + "/d"])
        b.rolls.append((r, other))
    around(b, rng.randint(0, 2))
    fh = rng.randint(max(0, now - b.keep(raw)), max(0, now - 73))
    b.correct(raw, fh)
    if rng.random() < 0.8:
        b.pin(p, b.fix[1] // 24)
    return b


def f_cross(rng):
    now = 24 * rng.randint(6, 14) + rng.choice([0, rng.randint(1, 23)])
    b = Build(rng, now)
    raw = b.src("h", 960)
    x = b.step("h", rng.choice([24, 48, 96]), [raw])
    d = b.step("d", rng.choice([96, 240]), [x + "-1", x + "/d"] if rng.random() < 0.5 else [x + "-1"])
    h = b.step("h", rng.choice([24, 48, 96]), [d + "-1", "%s~%d" % (x, rng.randint(2, 8))])
    b.step("d", rng.choice([96, 240]), [h + "/d", d + "~2"])
    around(b, rng.randint(1, 3))
    b.correct(raw, rng.randint(max(0, now - 120), now - 1))
    if rng.random() < 0.4:
        b.pin(d, b.fix[1] // 24 + rng.randint(0, 1))
    return b


def f_mixed(rng):
    b = rng.choice([f_reach, f_pins, f_stand, f_chain, f_window, f_lost, f_cross])(rng)
    around(b, rng.randint(1, 3))
    return b


def f_long(rng):
    """Three years of hourly history; thirty-day hourly windows; a correction eight to fifteen days back."""
    now = 24 * 1095 + rng.randint(0, 23)
    top = now // 24 - 1
    fd = top - rng.randint(8, 13)
    fh = hour_in(rng, fd)
    b = Build(rng, now)
    raw = b.src("h", 24 * 400)
    ref = b.src("d", 24 * 900)
    x = b.step("h", 48, [raw])
    a = b.step("h", 72, [x, "@-1"])
    w = b.step("h", 96, [x + "~720", ref + "-1"])
    r = b.step("d", 24 * 800, [x + "/d"])
    b.rolls.append((r, x))
    s = b.step("d", 24 * 800, [x + "/d", "@-1"])
    b.step("d", 24 * 800, [w + "/d", r + "~30"])
    b.step("h", 120, [w + "~168", a])
    b.step("h", 72, [x + "~720", ref + "-1"])
    b.correct(raw, fh)
    b.pin(a, fh - rng.randint(240, 288))
    b.pin(s, fd - rng.randint(15, 20))
    b.pin(r, fd + rng.randint(1, 3))
    return b


def f_deep(rng):
    """A long chain of expired hourly partitions, read through wide windows."""
    now = 24 * 1095 + rng.randint(0, 23)
    top = now // 24 - 1
    fd = top - rng.randint(5, 9)
    fh = hour_in(rng, fd)
    b = Build(rng, now)
    raw = b.src("h", 24 * 500)
    a = b.step("h", 24, [raw, "@-1"])
    w = b.step("h", 72, [a + "~720"])
    d = b.step("d", 24 * 800, [a + "/d", "@-1"])
    b.step("h", 96, [w + "~96", d + "-1"])
    b.step("d", 24 * 800, [w + "/d", d + "~14"])
    b.correct(raw, fh)
    b.pin(a, fh - rng.randint(24 * 40, 24 * 45))
    b.pin(d, fd - rng.randint(50, 55))
    return b


BUILDERS = {"plain": f_plain, "reach": f_reach, "pins": f_pins, "stand": f_stand,
            "chain": f_chain, "window": f_window, "edge": f_edge, "lost": f_lost,
            "cross": f_cross, "mixed": f_mixed, "long": f_long, "deep": f_deep}


def check(lines):
    """The rules the brief states for a pipeline file. A generated pipeline must keep them."""
    now, seen, grain, keep, reads, fix, rolls, pins = None, [], {}, {}, {}, None, [], []
    for line in lines:
        ws = line.split()
        if ws[0] == "now":
            now = int(ws[1])
        elif ws[0] in ("src", "step"):
            name, g = ws[1], ws[2]
            assert name not in grain and g in ("h", "d") and int(ws[3]) >= 1
            if ws[0] == "step":
                assert len(ws) > 4
                for tok in ws[4:]:
                    if tok.endswith("-1"):
                        src = tok[:-2]
                        assert src == name or src in grain
                        continue
                    if tok.endswith("/d"):
                        src = tok[:-2]
                        assert g == "d" and grain.get(src) == "h"
                        continue
                    src, _, width = tok.partition("~")
                    assert src in grain and src != name and grain[src] == g
                    assert not width or int(width) >= 2
                reads[name] = ws[4:]
            grain[name] = g
            keep[name] = int(ws[3])
            seen.append(name)
        elif ws[0] == "stand":
            rolls.append((ws[1], ws[2]))
        elif ws[0] == "pin":
            pins.append((ws[1], [int(p) for p in ws[2:]]))
        elif ws[0] == "fix":
            fix = (ws[1], int(ws[2]))
    assert now is not None and now >= 1 and fix is not None
    for roll, hourly in rolls:
        assert grain[roll] == "d" and grain[hourly] == "h" and reads.get(roll) == [hourly + "/d"]
    for name, parts in pins:
        assert name in reads
        for p in parts:
            assert p >= 0 and (p + 1 if grain[name] == "h" else 24 * p + 24) <= now
    name, p = fix
    assert name in grain and name not in reads
    end = p + 1 if grain[name] == "h" else 24 * p + 24
    assert p >= 0 and end <= now < end + keep[name], "the corrected partition must exist"


def build(fam, rng):
    """One pipeline of a family, as its lines; drawn again while its plan would be empty."""
    while True:
        lines = BUILDERS[fam](rng).lines()
        check(lines)
        if gets_a_line(lines):
            return lines


def gets_a_line(lines):
    """Whether the correction reaches a partition of a step that exists.

    The plan is empty exactly when it does not, because every such partition gets a line.
    This repeats the read arithmetic of the brief on its own, so the worker - which may not
    import the sealed model - can draw the same population the grader does.
    """
    names, grain, keep, reads, pins, now, fix = [], {}, {}, {}, set(), 0, None
    for line in lines:
        ws = line.split()
        if ws[0] == "now":
            now = int(ws[1])
        elif ws[0] in ("src", "step"):
            names.append(ws[1])
            grain[ws[1]] = ws[2]
            keep[ws[1]] = int(ws[3])
            if ws[0] == "step":
                reads[ws[1]] = ws[4:]
        elif ws[0] == "pin":
            pins.update((ws[1], int(p)) for p in ws[2:])
        elif ws[0] == "fix":
            fix = (ws[1], int(ws[2]))

    def end(n, i):
        return i + 1 if grain[n] == "h" else 24 * i + 24

    readers = {}
    for n in names:
        for tok in reads.get(n, ()):
            src = tok.split("/")[0].split("~")[0]
            src = src[:-2] if src.endswith("-1") else src
            readers.setdefault(src, []).append((n, tok))
    seen, todo = {fix}, [fix]
    while todo:
        src, i = todo.pop()
        for n, tok in readers.get(src, ()):
            if tok.endswith("/d"):
                outs = [i // 24]
            elif "~" in tok:
                outs = range(i, i + int(tok.split("~")[1]))
            elif tok.endswith("-1"):
                if grain[src] == grain[n]:
                    outs = [i + 1]
                elif grain[src] == "d":
                    outs = range(24 * (i + 1), 24 * (i + 2))
                else:
                    outs = [(i + 1) // 24] if (i + 1) % 24 == 0 else []
            else:
                outs = [i]
            for j in outs:
                if end(n, j) <= now and (n, j) not in seen:
                    seen.add((n, j))
                    todo.append((n, j))
    for n, j in seen:
        if n in reads and ((n, j) in pins or now < end(n, j) + keep[n]):
            return True
    return False


def programs(seed, per):
    """The graded population: `per` of each small family and BIG_EACH of each large one."""
    out = []
    for fam, big in FAMILIES:
        for k in range(BIG_EACH if big else per):
            rng = random.Random("%s|%s|%d" % (seed, fam, k))
            out.append((fam, "%s-%03d" % (fam, k), build(fam, rng)))
    return out
