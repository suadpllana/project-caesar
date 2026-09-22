"""The plainest reading of the contract, written for checking and never shipped.

Everything is recomputed from the tree every time it is needed: a full relayout per question,
a scan of every box for the stuck set. That makes it the naive-but-correct family the resource
gate exists to kill, and the ground truth the sealed model, the reference and the variants are
all diffed against on small programs. It shares no code with any of them.

    python3 naive.py prog.txt
"""
import sys

STATS = None


def note(key):
    if STATS is not None:
        STATS[key] = STATS.get(key, 0) + 1


class Box:
    def __init__(self, bid, own, flags):
        self.id = bid
        self.own = own
        self.pin = None
        self.shut = False
        self.lift = False
        self.live = False
        self.kids = []
        self.par = None
        self.gone = False
        for f in flags:
            if f.startswith("pin="):
                self.pin = int(f[4:])
            elif f == "shut":
                self.shut = True
            elif f == "lift":
                self.lift = True
            elif f == "live":
                self.live = True
            else:
                raise ValueError("flag %s" % f)


class Doc:
    def __init__(self):
        self.top = []          # top-level boxes in order
        self.by = {}
        self.vh = 0

    def kids_of(self, b):
        return self.top if b is None else b.kids

    # ---- layout, recomputed from scratch -------------------------------------------------
    def layout(self):
        """(tops, heights, doc height) for every laid-out box."""
        tops, hs = {}, {}

        def height(b):
            h = b.own
            if not b.shut:
                for c in b.kids:
                    if not c.lift:
                        h += height(c)
            hs[b] = h
            return h

        def place(b, y):
            tops[b] = y
            if b.shut:
                return
            y += b.own
            for c in b.kids:
                if c.lift:
                    continue
                place(c, y)
                y += hs[c]

        y = 0
        for b in self.top:
            if b.lift:
                continue
            height(b)
            place(b, y)
            y += hs[b]
        return tops, hs, y

    def laid_out(self, b, tops):
        return b in tops

    def section_end(self, b, tops, hs, dh):
        if b.par is None:
            return dh
        return tops[b.par] + hs[b.par]

    def stuck_at(self, s, tops, hs, dh):
        """{box: drawn top} for every stuck box at offset s."""
        out = {}
        for b in tops:
            if b.pin is None or hs[b] <= 0:
                continue
            r = min(s + b.pin, self.section_end(b, tops, hs, dh) - hs[b])
            if r > tops[b]:
                out[b] = r
        return out

    def band(self, s, stuck, hs):
        best = 0
        for b, r in stuck.items():
            best = max(best, r + hs[b] - s)
        return best

    def inside_stuck(self, b, stuck):
        x = b
        while x is not None:
            if x in stuck:
                return True
            x = x.par
        return False

    # ---- the pick before the edits --------------------------------------------------------
    def pick(self, s):
        tops, hs, dh = self.layout()
        stuck = self.stuck_at(s, tops, hs, dh)
        band = self.band(s, stuck, hs)
        u, w = s + band, s + self.vh
        if u >= w:
            return None

        def examine(b):
            if b.lift or b.live or hs[b] == 0 or b in stuck:
                return None
            a = tops[b]
            e = a + hs[b]
            if e <= u or a >= w:
                return None
            if a >= u and e <= w:
                return b
            if not b.shut:
                for c in b.kids:
                    got = examine(c)
                    if got is not None:
                        return got
            return b

        for b in self.top:
            got = examine(b)
            if got is not None:
                chain = []
                x = got
                while x is not None:
                    chain.append((x, tops[x] - u))
                    x = x.par
                return chain
        return None

    # ---- edits ----------------------------------------------------------------------------
    def apply(self, op):
        k = op[0]
        if k == "to":
            return
        if k == "add":
            _, bid, pid, idx, own, flags = op
            b = Box(bid, own, flags)
            par = None if pid == "-" else self.by[pid]
            b.par = par
            if idx > len(self.kids_of(par)):
                raise ValueError("add %s: index %d past the end" % (bid, idx))
            self.kids_of(par).insert(idx, b)
            self.by[bid] = b
            return
        b = self.by[op[1]]
        if k == "size":
            b.own = op[2]
        elif k == "drop":
            self.kids_of(b.par).remove(b)
            stack = [b]
            while stack:
                x = stack.pop()
                x.gone = True
                del self.by[x.id]
                stack.extend(x.kids)
        elif k == "shut":
            b.shut = True
        elif k == "open":
            b.shut = False
        elif k == "pin":
            b.pin = op[2]
        elif k == "unpin":
            b.pin = None
        elif k == "lift":
            b.lift = True
        elif k == "sink":
            b.lift = False
        else:
            raise ValueError(k)

    def op_box(self, op):
        if op[0] == "to":
            return None
        return self.by.get(op[1])

    def is_live(self, b):
        x = b
        while x is not None:
            if x.live:
                return True
            x = x.par
        return False

    # ---- one frame ------------------------------------------------------------------------
    def frame(self, s0, ops):
        chain = self.pick(s0)
        asked = None
        touched_live = False
        for op in ops:
            if op[0] == "to":
                asked = op[1]
                continue
            if op[0] != "add":
                touched_live = touched_live or self.is_live(self.op_box(op))
            self.apply(op)
            if op[0] == "add":
                touched_live = touched_live or self.is_live(self.by[op[1]])
        tops, hs, dh = self.layout()
        top_max = max(0, dh - self.vh)

        def clamp(x):
            return min(max(x, 0), top_max)

        if asked is not None:
            note("off scroll")
            return clamp(asked), "off scroll"
        if touched_live:
            note("off live")
            return clamp(s0), "off live"
        if chain is None:
            note("none before")
            return clamp(s0), "none"
        s = s0
        hist = []
        holders = []
        for k in range(4):
            stuck = self.stuck_at(s, tops, hs, dh)
            band = self.band(s, stuck, hs)
            hold = None
            for x, d in chain:
                if x.gone or x not in tops or hs[x] <= 0 or self.inside_stuck(x, stuck):
                    continue
                hold = (x, d)
                break
            if hold is None:
                note("none in pass %d" % (k + 1))
                return clamp(s), "none"
            x, d = hold
            holders.append(x)
            if x is not chain[0][0]:
                note("fallback used")
            if len(set(holders)) > 1:
                note("holder changed mid-loop")
            tgt = clamp(tops[x] - d - band)
            if tgt != tops[x] - d - band:
                note("clamped pass")
            if tgt == s:
                note("settled in pass %d" % (k + 1))
                return s, x.id
            hist.append((tgt, x))
            s = tgt
        note("four passes, no settle")
        best = min(t for t, _ in hist)
        for t, x in hist:
            if t == best:
                return t, x.id
        raise AssertionError("unreachable")


def parse(text):
    doc = Doc()
    frames = []
    at = None
    for raw in text.splitlines():
        p = raw.split()
        if not p:
            continue
        h = p[0]
        if h == "view":
            doc.vh = int(p[1])
        elif h == "box":
            b = Box(p[1], int(p[3]), p[4:])
            b.par = None if p[2] == "-" else doc.by[p[2]]
            doc.kids_of(b.par).append(b)
            doc.by[b.id] = b
        elif h == "at":
            at = int(p[1])
        elif h == "frame":
            frames.append([])
        elif h == "size":
            frames[-1].append(("size", p[1], int(p[2])))
        elif h == "add":
            frames[-1].append(("add", p[1], p[2], int(p[3]), int(p[4]), p[5:]))
        elif h in ("drop", "shut", "open", "unpin", "lift", "sink"):
            frames[-1].append((h, p[1]))
        elif h == "pin":
            frames[-1].append(("pin", p[1], int(p[2])))
        elif h == "to":
            frames[-1].append(("to", int(p[1])))
        else:
            raise ValueError("unknown statement %s" % h)
    return doc, at, frames


def run(text):
    doc, s, frames = parse(text)
    out = []
    for n, ops in enumerate(frames, 1):
        s, tag = doc.frame(s, ops)
        out.append("%d %d %s" % (n, s, tag))
    return out


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as fh:
        for line in run(fh.read()):
            print(line)
