#!/usr/bin/env python3
"""Scale program builders, measured here before the gate is written into anything. Never ships.

Two shapes, because a full relayout per frame is slow for two different reasons:

  long   a hundred chapters of twenty sections of a dozen rows, with a header in every
         chapter and every section - depth and header count
  wide   a dozen sections of a few thousand rows each - row width

Both keep the view wandering: every few dozen frames an explicit scroll moves it to a new place,
and the edits in between cluster around wherever it is, above it, in it and below it, so the
holder, the band and the fallback all have work to do on most frames.

    python3 scale.py time      naive, shipped, reference and model on one program of each
"""
import random
import sys
import time


class Sh:
    """Ids, parents and own heights of the program being written, in document order."""

    def __init__(self):
        self.n = 0
        self.par = {}
        self.kids = {"-": []}
        self.own = {}
        self.pin = {}
        self.lift = set()
        self.shut = set()

    def new(self, tag, par, own, at=None, pin=None):
        self.n += 1
        bid = "%s%d" % (tag, self.n)
        self.par[bid] = par
        self.kids[bid] = []
        row = self.kids[par]
        row.insert(len(row) if at is None else at, bid)
        self.own[bid] = own
        if pin is not None:
            self.pin[bid] = pin
        return bid

    def drop(self, bid):
        self.kids[self.par[bid]].remove(bid)
        todo = [bid]
        while todo:
            x = todo.pop()
            todo.extend(self.kids.pop(x))
            del self.par[x]
            del self.own[x]
            self.pin.pop(x, None)
            self.lift.discard(x)
            self.shut.discard(x)

    def tops(self):
        """Tops of every laid-out box, by a plain walk; used rarely, to aim a scroll."""
        out = {}
        y = 0
        stack = [(b, 0) for b in reversed(self.kids["-"])]
        acc = [0]

        def walk(b, y):
            if b in self.lift:
                return 0
            out[b] = y
            h = self.own[b]
            if b not in self.shut:
                for c in self.kids[b]:
                    h += walk(c, y + h)
            return h

        for b in self.kids["-"]:
            y += walk(b, y)
        del stack, acc
        return out, y


def decl(sh, lines, bid):
    par = sh.par[bid]
    fl = []
    if bid in sh.pin:
        fl.append("pin=%d" % sh.pin[bid])
    lines.append(" ".join(["box", bid, par, str(sh.own[bid])] + fl))


def build_long(rng, chapters=100, sections=20, rows=12):
    sh = Sh()
    order = []
    for _c in range(chapters):
        c = sh.new("c", "-", 30)
        order.append(c)
        order.append(sh.new("h", c, 36, pin=0))
        for _s in range(sections):
            s = sh.new("s", c, 12)
            order.append(s)
            order.append(sh.new("h", s, 28, pin=36))
            for _r in range(rows):
                r = sh.new("r", s, rng.choice([20, 24, 40, 60, 90, 140]))
                order.append(r)
                if rng.random() < 0.25:
                    for _k in range(rng.randint(1, 3)):
                        order.append(sh.new("r", r, rng.choice([16, 20, 30])))
    return sh, order, 800


def build_wide(rng, sections=12, rows=3000):
    sh = Sh()
    order = []
    for _s in range(sections):
        s = sh.new("s", "-", 20)
        order.append(s)
        order.append(sh.new("h", s, 32, pin=0))
        for i in range(rows):
            if i % 100 == 50:
                part = sh.new("p", s, 14)
                order.append(part)
                order.append(sh.new("h", part, 24, pin=32))
                for _k in range(rng.randint(2, 5)):
                    order.append(sh.new("r", part, rng.choice([18, 22, 36])))
            else:
                order.append(sh.new("r", s, rng.choice([18, 22, 36, 54, 80])))
    return sh, order, 600


def frames(rng, sh, vh, count, lines):
    """Edits clustered around a wandering view, with an explicit scroll every few dozen."""
    rows = [b for b in sh.par if b.startswith("r")]
    focus = None
    for f in range(count):
        lines.append("frame")
        if focus is None or f % 40 == 0:
            tops, end = sh.tops()
            live_rows = [b for b in rows if b in sh.par and b in tops]
            focus = rng.choice(live_rows)
            lines.append("to %d" % max(0, min(tops[focus] - rng.randint(0, vh // 2), end - vh)))
            continue
        near = sh.kids[sh.par[focus]] if sh.par.get(focus, "-") != "-" else sh.kids["-"]
        for _e in range(rng.randint(1, 3)):
            pool = [b for b in near if b in sh.par and not b.startswith("h")]
            k = rng.random()
            if not pool or k < 0.1:
                par = sh.par.get(focus, "-")
                if par not in sh.kids:
                    par = "-"
                at = rng.randint(0, len(sh.kids[par]))
                bid = sh.new("r", par, rng.choice([20, 30, 60]), at=at)
                rows.append(bid)
                lines.append("add %s %s %d %d" % (bid, par, at, sh.own[bid]))
                continue
            b = rng.choice(pool)
            if k < 0.7:
                sh.own[b] = rng.choice([0, 20, 30, 60, 120, 200])
                lines.append("size %s %d" % (b, sh.own[b]))
            elif k < 0.78 and b != focus:
                sh.drop(b)
                lines.append("drop %s" % b)
            elif k < 0.86:
                if b in sh.shut:
                    sh.shut.discard(b)
                    lines.append("open %s" % b)
                else:
                    sh.shut.add(b)
                    lines.append("shut %s" % b)
            elif k < 0.92:
                if b in sh.lift:
                    sh.lift.discard(b)
                    lines.append("sink %s" % b)
                else:
                    sh.lift.add(b)
                    lines.append("lift %s" % b)
            else:
                hs = [x for x in near if x in sh.pin]
                if hs:
                    h = rng.choice(hs)
                    sh.own[h] = rng.choice([20, 28, 40])
                    lines.append("size %s %d" % (h, sh.own[h]))


def program(kind, rng, count):
    sh, order, vh = (build_long if kind == "long" else build_wide)(rng)
    lines = ["view %d" % vh]
    for bid in order:
        decl(sh, lines, bid)
    lines.append("at 0")
    frames(rng, sh, vh, count, lines)
    return lines


def main(argv):
    sys.path.insert(0, "/home/user/project-caesar/authoring/anchor-band-settle")
    import lab
    cases, gen, model = lab.sealed()
    naive = lab.naive()
    count = int(argv[2]) if len(argv) > 2 else 1500
    for kind in ("long", "wide"):
        t = time.time()
        lines = program(kind, random.Random("scale|" + kind), count)
        text = "\n".join(lines) + "\n"
        print("%s: %d statements, %d boxes, built in %.1fs"
              % (kind, len(lines), sum(1 for x in lines if x.startswith("box")), time.time() - t),
              flush=True)
        t = time.time()
        want = model.expect(lines)
        print("  model      %.2fs" % (time.time() - t), flush=True)
        for name, d in (("reference", lab.SOL), ("shipped", None)):
            here = lab.tree(d)
            t = time.time()
            got = lab.run_shell(here, text, timeout=900)
            print("  %-10s %.2fs  %s" % (name, time.time() - t,
                                        "agrees" if got == want else "DIFFERS (%s)" % got[:1]),
                  flush=True)
        if "naive" in argv:
            t = time.time()
            got = naive.run(text)
            print("  naive      %.2fs  %s" % (time.time() - t, "agrees" if got == want else "DIFFERS"),
                  flush=True)


if __name__ == "__main__":
    main(sys.argv)
