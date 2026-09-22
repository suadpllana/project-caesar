"""Page scripts generated inside the verifier, from a seed drawn after the agent has finished.

Every family is shaped around one part of the model rather than left to chance, because an
unshaped population barely exercises the rules that matter: an event-driven reader and the
specified one agree on any page whose updates are spaced further apart than their speech takes.

  plain  updates spaced out past their speech, in polite and assertive regions: the ordinary
         side of every fence, where nothing overlaps and each change is spoken exactly once
  crowd  polite regions edited while their speech is still playing: stale text, undone edits
         and changes that pile up behind a long utterance
  cut    assertive regions interrupting polite speech, with the cut text edited or undone before
         the alert finishes
  atom   aria-atomic true and false nested inside regions, set and cleared while speech plays,
         with removals relevant so that removals re-read their units
  busy   aria-busy on region elements and on containers inside them, released later, with
         nodes moved out of held containers and removals placed under them, busy containers
         inside atomic ones, and aria-busy on the element that holds the regions, where it
         holds nothing
  hide   hidden and aria-hidden on containers and regions, hidden with the value false, which
         still hides, aria-hidden false beneath a hidden ancestor, and regions switched between
         polite, assertive and off
  move   nodes moved inside a region and then dropped, and nodes moved between regions
  rel    aria-relevant on region elements in every combination, and on inner elements where it
         means nothing
  mix    all of the above at once
  wide   a large page with light activity across many regions for thousands of ticks
  held   a busy container gathering thousands of differences while another region keeps the
         reader speaking, then released
"""
import random

FAMILIES = (
    ("plain", False),
    ("crowd", False),
    ("cut", False),
    ("atom", False),
    ("busy", False),
    ("hide", False),
    ("move", False),
    ("rel", False),
    ("mix", False),
    ("wide", True),
    ("held", True),
)

BIG_EACH = 3

WORDS = (
    "ready saving saved sent new mail error retry done loading items page next back open "
    "closed low high update alert note list row cart total price item added cleared queued "
    "online offline syncing synced paused playing muted one two three four five six seven "
    "eight nine ten away busy typing joined left upload download failed passed warning"
).split()

RELS = ("", "additions", "removals", "text", "all", "additions removals", "additions text",
        "removals text", "text additions removals", "bogus", "bogus removals")


class Sketch:
    def __init__(self, rng, last):
        self.rng = rng
        self.last = last
        self.par = {0: None}
        self.kid = {0: []}
        self.txt = {}
        self.att = {0: {}}
        self.nid = 1
        self.regions = []
        self.hist = {}
        self.out = {0: []}
        self.tick = 0

    def at(self, t):
        self.tick = t
        self.out.setdefault(t, [])

    def emit(self, line):
        self.out[self.tick].append(line)

    def words(self, lo=1, hi=4):
        return " ".join(self.rng.choice(WORDS) for _ in range(self.rng.randint(lo, hi)))

    def _place(self, p, pos):
        ks = self.kid[p]
        if pos is None or pos >= len(ks):
            ks.append(None)
            return len(ks) - 1, "end" if pos is None else str(len(ks) - 1)
        ks.insert(pos, None)
        return pos, str(pos)

    def el(self, p, tag, pos=None):
        n = self.nid
        self.nid += 1
        i, tok = self._place(p, pos)
        self.kid[p][i] = n
        self.par[n] = p
        self.kid[n] = []
        self.att[n] = {}
        self.emit("add %d %d %s el %s" % (n, p, tok, tag))
        return n

    def tx(self, p, words=None, pos=None):
        n = self.nid
        self.nid += 1
        w = words or self.words()
        i, tok = self._place(p, pos)
        self.kid[p][i] = n
        self.par[n] = p
        self.txt[n] = w
        self.hist[n] = [w]
        self.emit("add %d %d %s tx %s" % (n, p, tok, w))
        return n

    def set(self, e, name, value):
        self.att[e][name] = value
        self.emit("set %d %s %s" % (e, name, value))

    def unset(self, e, name):
        self.att[e].pop(name, None)
        self.emit("unset %d %s" % (e, name))

    def text(self, n, words=None):
        w = words or self.words()
        self.txt[n] = w
        self.hist[n].append(w)
        self.emit("text %d %s" % (n, w))

    def undo(self, n):
        h = self.hist[n]
        if len(h) < 2:
            return self.text(n)
        w = self.rng.choice(h[:-1])
        self.text(n, w)

    def attached(self, n):
        while n is not None:
            if n == 0:
                return True
            n = self.par[n]
        return False

    def under(self, n, top):
        while n is not None:
            if n == top:
                return True
            n = self.par[n]
        return False

    def move(self, n, p, pos=None):
        old = self.par[n]
        self.kid[old].remove(n)
        ks = self.kid[p]
        if pos is None or pos >= len(ks):
            ks.append(n)
            tok = "end" if pos is None else str(len(ks) - 1)
        else:
            ks.insert(pos, n)
            tok = str(pos)
        self.par[n] = p
        self.emit("move %d %d %s" % (n, p, tok))

    def drop(self, n):
        self.kid[self.par[n]].remove(n)
        self.par[n] = None
        self.emit("drop %d" % n)

    def _below(self, top):
        todo = [top]
        while todo:
            x = todo.pop()
            yield x
            todo.extend(self.kid.get(x, ()))

    def texts(self, within):
        if within is None or not self.attached(within):
            return []
        return [n for n in self._below(within) if n in self.txt]

    def boxes(self, within):
        if within is None or not self.attached(within):
            return []
        return [n for n in self._below(within) if n in self.kid and n != within]

    def lines(self):
        out = ["page %d" % self.last]
        for t in sorted(self.out):
            if t == 0 or self.out[t]:
                out.append("@%d" % t)
                out.extend(self.out[t])
        return out


def _region(sk, host, live, rng, rel=None, atom=None, busy=False):
    r = sk.el(host, rng.choice(("div", "section", "aside")))
    sk.set(r, "aria-live", live)
    sk.regions.append(r)
    if rel:
        sk.set(r, "aria-relevant", rel)
    if atom:
        sk.set(r, "aria-atomic", atom)
    if busy:
        sk.set(r, "aria-busy", "true")
    return r


def _fill(sk, box, rng, texts, kids=0, depth=1):
    for _ in range(texts):
        sk.tx(box)
    for _ in range(kids):
        c = sk.el(box, rng.choice(("span", "p", "ul", "li", "div")))
        _fill(sk, c, rng, rng.randint(1, 3), rng.randint(0, 1) if depth < 3 else 0, depth + 1)


def _page(sk, rng, live, extra=0):
    head = sk.el(0, "header")
    sk.tx(head, "welcome")
    main = sk.el(0, "main")
    regs = []
    for v in live:
        r = _region(sk, main, v, rng)
        _fill(sk, r, rng, rng.randint(1, 3), rng.randint(0, 2))
        regs.append(r)
    for _ in range(extra):
        box = sk.el(main, "div")
        _fill(sk, box, rng, rng.randint(1, 2), rng.randint(0, 1))
    return head, main, regs


def _pick(rng, xs):
    return rng.choice(xs) if xs else None


def _edit(sk, rng, within=None, undo=0.25):
    ts = sk.texts(within)
    n = _pick(rng, ts)
    if n is None:
        return
    if rng.random() < undo:
        sk.undo(n)
    else:
        sk.text(n)


def _grow(sk, rng, within):
    bs = [within] + sk.boxes(within)
    b = _pick(rng, bs)
    if rng.random() < 0.7:
        sk.tx(b, pos=rng.choice((None, 0, 1)))
    else:
        c = sk.el(b, rng.choice(("li", "span", "p")), pos=rng.choice((None, 0)))
        for _ in range(rng.randint(1, 2)):
            sk.tx(c)


def _shrink(sk, rng, within):
    xs = [n for n in sk.texts(within)] + [b for b in sk.boxes(within) if b not in sk.regions]
    n = _pick(rng, xs)
    if n is not None and n != within:
        sk.drop(n)


def _shift(sk, rng, within, into):
    xs = [n for n in sk.texts(within)] + [b for b in sk.boxes(within) if b not in sk.regions]
    n = _pick(rng, xs)
    if n is None or n == within:
        return
    targets = [b for b in [into] + sk.boxes(into) if not sk.under(b, n)]
    p = _pick(rng, targets)
    if p is None:
        return
    sk.move(n, p, pos=rng.choice((None, 0)))


def fam_plain(rng):
    sk = Sketch(rng, rng.randint(40, 80))
    _h, _m, regs = _page(sk, rng, ["polite", "assertive", "polite"][:rng.randint(1, 3)])
    t = 1
    while True:
        t += rng.randint(6, 12)
        if t > sk.last:
            break
        sk.at(t)
        r = _pick(rng, regs)
        if rng.random() < 0.6:
            _edit(sk, rng, r, undo=0)
        else:
            sk.tx(r)
    return sk


def fam_crowd(rng):
    sk = Sketch(rng, rng.randint(50, 90))
    _h, _m, regs = _page(sk, rng, ["polite", "polite"])
    for t in range(1, sk.last + 1):
        if rng.random() < 0.55:
            sk.at(t)
            for _ in range(rng.randint(1, 2)):
                r = _pick(rng, regs)
                x = rng.random()
                if x < 0.5:
                    _edit(sk, rng, r, undo=0.35)
                elif x < 0.8:
                    _grow(sk, rng, r)
                else:
                    _shrink(sk, rng, r)
    return sk


def fam_cut(rng):
    sk = Sketch(rng, rng.randint(50, 90))
    _h, _m, regs = _page(sk, rng, ["polite", "assertive", "polite"])
    pol = [regs[0], regs[2]]
    loud = regs[1]
    if rng.random() < 0.5:
        sk.set(pol[0], "aria-atomic", "true")
    for t in range(1, sk.last + 1):
        x = rng.random()
        if x < 0.35:
            sk.at(t)
            r = _pick(rng, pol)
            if rng.random() < 0.6:
                _edit(sk, rng, r, undo=0.3)
            else:
                _grow(sk, rng, r)
        elif x < 0.5:
            sk.at(t)
            if rng.random() < 0.7:
                _edit(sk, rng, loud, undo=0.2)
            else:
                _grow(sk, rng, loud)
        elif x < 0.58:
            sk.at(t)
            _edit(sk, rng, _pick(rng, pol), undo=0.8)
    return sk


def _containers(sk, rng, regs, n):
    out = []
    for _ in range(n):
        r = _pick(rng, regs)
        host = _pick(rng, [r] + sk.boxes(r))
        c = sk.el(host, rng.choice(("div", "ul", "p")))
        _fill(sk, c, rng, rng.randint(1, 3), rng.randint(0, 1))
        out.append(c)
    return out


def fam_atom(rng):
    sk = Sketch(rng, rng.randint(50, 90))
    _h, _m, regs = _page(sk, rng, ["polite", "polite", "assertive"])
    for r in regs:
        if rng.random() < 0.6:
            sk.set(r, "aria-relevant", rng.choice(("all", "additions removals", "removals text")))
        if rng.random() < 0.4:
            sk.set(r, "aria-atomic", rng.choice(("true", "false")))
    boxes = _containers(sk, rng, regs, rng.randint(2, 4))
    for b in boxes:
        v = rng.choice(("true", "false", "true", None))
        if v:
            sk.set(b, "aria-atomic", v)
    for t in range(1, sk.last + 1):
        x = rng.random()
        if x < 0.5:
            sk.at(t)
            r = _pick(rng, regs)
            y = rng.random()
            if y < 0.45:
                _edit(sk, rng, r, undo=0.2)
            elif y < 0.7:
                _grow(sk, rng, r)
            else:
                _shrink(sk, rng, r)
        elif x < 0.6:
            sk.at(t)
            b = _pick(rng, [b for b in boxes if sk.attached(b)] + regs)
            v = rng.choice(("true", "false", None))
            if v:
                sk.set(b, "aria-atomic", v)
            else:
                sk.unset(b, "aria-atomic")
    return sk


def fam_busy(rng):
    sk = Sketch(rng, rng.randint(60, 100))
    _h, main, regs = _page(sk, rng, ["polite", "polite", "assertive"])
    for r in regs:
        if rng.random() < 0.5:
            sk.set(r, "aria-relevant", "all")
    boxes = _containers(sk, rng, regs, rng.randint(2, 4))
    units, inners = [], []
    for i, b in enumerate(list(boxes)):
        if i == 0 or rng.random() < 0.3:
            sk.set(b, "aria-atomic", "true")
            if rng.random() < 0.7:
                inner = sk.el(b, rng.choice(("ul", "p")))
                _fill(sk, inner, rng, rng.randint(1, 2))
                sk.set(inner, "aria-busy", "true")
                boxes.append(inner)
                units.append(b)
                inners.append(inner)
    for t in range(1, sk.last + 1):
        x = rng.random()
        if x < 0.12:
            sk.at(t)
            if inners and rng.random() < 0.5:
                b = _pick(rng, inners)
            else:
                b = _pick(rng, [b for b in boxes if sk.attached(b)] + regs + [main])
            if not sk.attached(b):
                continue
            if sk.att[b].get("aria-busy") == "true":
                if rng.random() < 0.2:
                    sk.set(b, "aria-busy", "false")
                else:
                    sk.unset(b, "aria-busy")
            else:
                sk.set(b, "aria-busy", "true")
        elif x < 0.55:
            sk.at(t)
            r = _pick(rng, regs)
            y = rng.random()
            if y < 0.4:
                _edit(sk, rng, r, undo=0.2)
            elif y < 0.65:
                _grow(sk, rng, r)
            elif y < 0.85:
                _shift(sk, rng, r, r)
            else:
                _shrink(sk, rng, r)
        elif x < 0.75 and units:
            sk.at(t)
            _edit(sk, rng, _pick(rng, [b for b in units if sk.attached(b)]), undo=0.2)
    return sk


def fam_hide(rng):
    sk = Sketch(rng, rng.randint(50, 90))
    _h, main, regs = _page(sk, rng, ["polite", "assertive", "off", "polite"][:rng.randint(2, 4)], 1)
    for r in regs:
        if rng.random() < 0.4:
            sk.set(r, "aria-relevant", "all")
    boxes = _containers(sk, rng, regs, rng.randint(2, 4))
    wrap = sk.el(main, "div")
    inner = _region(sk, wrap, rng.choice(("polite", "off")), rng)
    _fill(sk, inner, rng, 2, 1)
    regs.append(inner)
    hidable = boxes + regs + [wrap]
    for t in range(1, sk.last + 1):
        x = rng.random()
        if x < 0.2:
            sk.at(t)
            b = _pick(rng, [b for b in hidable if sk.attached(b)])
            if b is None:
                continue
            name = rng.choice(("hidden", "aria-hidden", "aria-hidden"))
            if name in sk.att[b]:
                if name == "aria-hidden" and rng.random() < 0.3:
                    sk.set(b, name, "false")
                else:
                    sk.unset(b, name)
            else:
                sk.set(b, name, "true" if name == "aria-hidden" else
                       rng.choice(("true", "hidden", "false")))
        elif x < 0.28:
            sk.at(t)
            r = _pick(rng, regs)
            sk.set(r, "aria-live", rng.choice(("polite", "assertive", "off")))
        elif x < 0.6:
            sk.at(t)
            r = _pick(rng, regs)
            y = rng.random()
            if y < 0.5:
                _edit(sk, rng, r, undo=0.2)
            elif y < 0.8:
                _grow(sk, rng, r)
            else:
                _shrink(sk, rng, r)
    return sk


def fam_move(rng):
    sk = Sketch(rng, rng.randint(50, 90))
    _h, _m, regs = _page(sk, rng, ["polite", "polite", "assertive"])
    for r in regs:
        if rng.random() < 0.7:
            sk.set(r, "aria-relevant", rng.choice(("all", "additions removals")))
    boxes = _containers(sk, rng, regs, rng.randint(3, 5))
    for b in boxes:
        if rng.random() < 0.4:
            sk.set(b, "aria-atomic", "true")
        elif rng.random() < 0.2:
            sk.set(b, "aria-busy", "true")
    for t in range(1, sk.last + 1):
        x = rng.random()
        if x < 0.3:
            sk.at(t)
            r = _pick(rng, regs)
            _shift(sk, rng, r, r)
        elif x < 0.42:
            sk.at(t)
            a, b = rng.sample(regs, 2)
            _shift(sk, rng, a, b)
        elif x < 0.55:
            sk.at(t)
            _shrink(sk, rng, _pick(rng, regs))
        elif x < 0.7:
            sk.at(t)
            r = _pick(rng, regs)
            if rng.random() < 0.5:
                _edit(sk, rng, r)
            else:
                _grow(sk, rng, r)
        elif x < 0.75:
            sk.at(t)
            b = _pick(rng, [b for b in boxes if sk.attached(b)])
            if b is not None:
                if "aria-busy" in sk.att[b]:
                    sk.unset(b, "aria-busy")
                else:
                    sk.set(b, "aria-busy", "true")
    return sk


def fam_rel(rng):
    sk = Sketch(rng, rng.randint(50, 90))
    _h, _m, regs = _page(sk, rng, ["polite", "polite", "assertive"])
    for r in regs:
        v = rng.choice(RELS)
        if v:
            sk.set(r, "aria-relevant", v)
    boxes = _containers(sk, rng, regs, rng.randint(2, 4))
    for b in boxes:
        if rng.random() < 0.6:
            sk.set(b, "aria-relevant", rng.choice(("all", "removals", "text")))
    for t in range(1, sk.last + 1):
        x = rng.random()
        if x < 0.5:
            sk.at(t)
            r = _pick(rng, regs)
            y = rng.random()
            if y < 0.35:
                _edit(sk, rng, r, undo=0.3)
            elif y < 0.6:
                _grow(sk, rng, r)
            elif y < 0.85:
                _shrink(sk, rng, r)
            else:
                _shift(sk, rng, r, _pick(rng, regs))
        elif x < 0.57:
            sk.at(t)
            r = _pick(rng, regs)
            v = rng.choice(RELS)
            if v:
                sk.set(r, "aria-relevant", v)
            else:
                sk.unset(r, "aria-relevant")
    return sk


def fam_mix(rng):
    sk = Sketch(rng, rng.randint(70, 120))
    _h, main, regs = _page(sk, rng, ["polite", "assertive", "polite", "off"], 1)
    for r in regs:
        v = rng.choice(RELS)
        if v:
            sk.set(r, "aria-relevant", v)
    boxes = _containers(sk, rng, regs, rng.randint(3, 6))
    for b in boxes:
        v = rng.random()
        if v < 0.3:
            sk.set(b, "aria-atomic", rng.choice(("true", "false")))
        elif v < 0.45:
            sk.set(b, "aria-busy", "true")
    ops = ("edit", "edit", "grow", "shrink", "shift", "cross", "busy", "hide", "live", "atom", "rel")
    for t in range(1, sk.last + 1):
        if rng.random() < 0.55:
            sk.at(t)
            op = rng.choice(ops)
            r = _pick(rng, regs)
            if op == "edit":
                _edit(sk, rng, r, undo=0.3)
            elif op == "grow":
                _grow(sk, rng, r)
            elif op == "shrink":
                _shrink(sk, rng, r)
            elif op == "shift":
                _shift(sk, rng, r, r)
            elif op == "cross":
                _shift(sk, rng, r, _pick(rng, regs))
            elif op == "busy":
                b = _pick(rng, [b for b in boxes if sk.attached(b)] + regs)
                if "aria-busy" in sk.att[b]:
                    sk.unset(b, "aria-busy")
                else:
                    sk.set(b, "aria-busy", "true")
            elif op == "hide":
                b = _pick(rng, [b for b in boxes if sk.attached(b)] + regs)
                if "hidden" in sk.att[b]:
                    sk.unset(b, "hidden")
                elif "aria-hidden" in sk.att[b]:
                    sk.unset(b, "aria-hidden")
                else:
                    sk.set(b, rng.choice(("hidden", "aria-hidden")), "true")
            elif op == "live":
                sk.set(r, "aria-live", rng.choice(("polite", "assertive", "off")))
            elif op == "atom":
                b = _pick(rng, [b for b in boxes if sk.attached(b)] + regs)
                v = rng.choice(("true", "false", None))
                if v:
                    sk.set(b, "aria-atomic", v)
                else:
                    sk.unset(b, "aria-atomic")
            else:
                v = rng.choice(RELS)
                if v:
                    sk.set(r, "aria-relevant", v)
                else:
                    sk.unset(r, "aria-relevant")
    return sk


def fam_wide(rng):
    sk = Sketch(rng, 2400)
    main = sk.el(0, "main")
    regs = []
    for i in range(56):
        r = _region(sk, main, rng.choice(("polite", "polite", "assertive", "off")), rng,
                    rel=rng.choice(("", "all", "additions text")) or None)
        regs.append(r)
        for _ in range(12):
            box = sk.el(r, "ul")
            for _ in range(12):
                li = sk.el(box, "li")
                sk.tx(li, sk.words(1, 2))
                sk.tx(li, sk.words(1, 1))
    for _ in range(16):
        box = sk.el(main, "div")
        for _ in range(60):
            sk.tx(box, sk.words(1, 2))
    for t in range(1, sk.last + 1):
        if rng.random() < 0.6:
            sk.at(t)
            r = _pick(rng, regs)
            x = rng.random()
            if x < 0.5:
                _edit(sk, rng, _pick(rng, sk.kid[r]) if sk.kid[r] else r, undo=0.2)
            elif x < 0.75:
                box = _pick(rng, sk.kid[r])
                if box is not None:
                    li = sk.el(box, "li", pos=0)
                    sk.tx(li, sk.words(1, 2))
            elif x < 0.9:
                box = _pick(rng, sk.kid[r])
                if box is not None and sk.kid[box]:
                    sk.drop(_pick(rng, sk.kid[box]))
            else:
                box = _pick(rng, sk.kid[r])
                if box is not None:
                    if "aria-busy" in sk.att[box]:
                        sk.unset(box, "aria-busy")
                    else:
                        sk.set(box, "aria-busy", "true")
    return sk


def fam_held(rng):
    sk = Sketch(rng, 3000)
    main = sk.el(0, "main")
    log = _region(sk, main, "polite", rng, rel="all")
    hold = sk.el(log, "ul")
    sk.set(hold, "aria-busy", "true")
    talk = _region(sk, main, "polite", rng)
    line = sk.tx(talk, "ready")
    rows = []
    release = rng.randint(2500, 2700)
    for t in range(1, sk.last + 1):
        sk.at(t)
        if t < release:
            for _ in range(6):
                li = sk.el(hold, "li", pos=0 if rng.random() < 0.3 else None)
                rows.append(sk.tx(li, sk.words(1, 1)))
            if rows and rng.random() < 0.3:
                sk.text(rng.choice(rows), sk.words(1, 1))
            sk.text(line, sk.words(1, 1))
        elif t == release:
            sk.unset(hold, "aria-busy")
        elif t % 7 == 0:
            sk.text(line, sk.words(1, 1))
    return sk


BUILD = {
    "plain": fam_plain, "crowd": fam_crowd, "cut": fam_cut, "atom": fam_atom, "busy": fam_busy,
    "hide": fam_hide, "move": fam_move, "rel": fam_rel, "mix": fam_mix, "wide": fam_wide,
    "held": fam_held,
}


def one(seed, fam, i):
    rng = random.Random("%s/%s/%d" % (seed, fam, i))
    return BUILD[fam](rng).lines()


def programs(seed, per):
    out = []
    for fam, big in FAMILIES:
        for i in range(BIG_EACH if big else per):
            out.append((fam, "%s-%03d" % (fam, i), one(seed, fam, i)))
    return out
