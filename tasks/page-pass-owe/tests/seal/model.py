"""What a list file must print, worked out a second time and a different way.

This is not the reference solution restructured; it is the contract implemented again so
that a submission agreeing with it agrees with the rules rather than with one author's
data structures. Where the reference keeps one flat ordered list of places per tag, this
keeps a sorted key list per tag with a sorted id list under each key, and walks it as key
blocks. Where the reference keeps a ledger as an insertion-ordered dict and removes from
the middle, this keeps an append-only list of (row, stamp) entries with a live map beside
it and steps the head over entries whose stamp is stale, which is what makes a row that
comes to be owed a second time land at the end for free. Where the reference carries one
owed total for the whole service, this carries one per scroll and adds them up.

The rules themselves, in the order a page applies them:

  order       a place is (key, id); smaller key first, smaller id among equal keys
  view        a scroll reads the rows carrying its tag at the moment it looks
  ledger      drained strictly from the front while the entry there fits
  empty page  a page that has handed out nothing takes the row in hand whatever it
              weighs, and spends the page's whole weight doing it
  scan        from strictly after the mark, in place order: rows already handed to this
              scroll are passed by, rows that fit go out, rows that do not are stepped
              over and come to be owed
  stops       the page is full, its weight is spent, the rows stepped over in this page
              weigh as much as a page carries, the view has no further row, or the hold
              has no room for the row in hand - and only that last one leaves the mark
              short of the row that stopped it
  mark        the place of the last row the scan looked at; draining never moves it
  owed        derived: the scroll's tag, a place at or before its mark, not yet handed
              out. Order is the order rows came to be owed, with a re-entry at the end
  hold        at most cfg weight owed across every scroll at once, and it governs what a
              scan may step over, never what an edit may bring to be owed
  memory      permanent, per scroll, by row id
"""

import bisect


class View(object):
    """The table, ordered per tag as a key list with an id list under each key."""

    def __init__(self):
        self.keys = {}
        self.ids = {}

    def put(self, g, k, i):
        ks = self.keys.setdefault(g, [])
        pool = self.ids.setdefault(g, {})
        at = bisect.bisect_left(ks, k)
        if at == len(ks) or ks[at] != k:
            ks.insert(at, k)
            pool[k] = []
        bisect.insort(pool[k], i)

    def take(self, g, k, i):
        pool = self.ids.get(g)
        if not pool or k not in pool:
            return
        row = pool[k]
        at = bisect.bisect_left(row, i)
        if at < len(row) and row[at] == i:
            del row[at]
        if not row:
            del pool[k]
            ks = self.keys[g]
            at = bisect.bisect_left(ks, k)
            if at < len(ks) and ks[at] == k:
                del ks[at]

    def walk(self, g, mk):
        """Places of tag g strictly after mk, in order. mk None means from the front."""
        ks = self.keys.get(g)
        if not ks:
            return
        pool = self.ids[g]
        if mk is None:
            kat, iat = 0, 0
        else:
            kat = bisect.bisect_left(ks, mk[0])
            if kat < len(ks) and ks[kat] == mk[0]:
                iat = bisect.bisect_right(pool[mk[0]], mk[1])
            else:
                iat = 0
        while kat < len(ks):
            row = pool[ks[kat]]
            k = ks[kat]
            while iat < len(row):
                yield (k, row[iat])
                iat += 1
            kat += 1
            iat = 0

    def members(self, g):
        ks = self.keys.get(g)
        if not ks:
            return
        pool = self.ids[g]
        for k in ks:
            for i in pool[k]:
                yield i


class Led(object):
    """Owed rows in the order they came to be owed, by stamp rather than by removal."""

    def __init__(self):
        self.order = []
        self.stamp = {}
        self.live = {}
        self.tick = 0
        self.head = 0
        self.tot = 0

    def add(self, i, w):
        if i in self.live:
            return
        self.tick += 1
        self.stamp[i] = self.tick
        self.live[i] = w
        self.tot += w
        self.order.append((i, self.tick))

    def rm(self, i):
        w = self.live.pop(i, None)
        if w is None:
            return
        self.tot -= w
        self.stamp.pop(i, None)

    def front(self):
        while self.head < len(self.order):
            i, t = self.order[self.head]
            if self.stamp.get(i) == t:
                return i
            self.head += 1
        return None

    def count(self):
        return len(self.live)


class Scroll(object):
    def __init__(self, s, g, n, c):
        self.s = s
        self.g = g
        self.n = n
        self.c = c
        self.mk = None
        self.led = Led()
        self.got = set()


class Run(object):
    def __init__(self, hold):
        self.hold = hold
        self.rows = {}
        self.view = View()
        self.scrolls = {}
        self.at_tag = {}
        self.out = []

    # -- the derived membership rule, asked again wherever an input to it changed ----

    def owed_now(self, sc, i):
        r = self.rows.get(i)
        if r is None or r[1] != sc.g or i in sc.got:
            return False
        return sc.mk is not None and (r[0], i) <= sc.mk

    def settle(self, sc, i):
        if self.owed_now(sc, i):
            sc.led.add(i, self.rows[i][2])
        else:
            sc.led.rm(i)

    def standing(self):
        total = 0
        for s in self.scrolls:
            total += self.scrolls[s].led.tot
        return total

    # -- edits -----------------------------------------------------------------------

    def add(self, i, k, g, w):
        self.rows[i] = (k, g, w)
        self.view.put(g, k, i)
        for sc in self.at_tag.get(g, ()):
            self.settle(sc, i)

    def move(self, i, k):
        r = self.rows.get(i)
        if r is None:
            return
        self.view.take(r[1], r[0], i)
        self.rows[i] = (k, r[1], r[2])
        self.view.put(r[1], k, i)
        for sc in self.at_tag.get(r[1], ()):
            self.settle(sc, i)

    def retag(self, i, g):
        r = self.rows.get(i)
        if r is None:
            return
        self.view.take(r[1], r[0], i)
        self.rows[i] = (r[0], g, r[2])
        self.view.put(g, r[0], i)
        if g != r[1]:
            for sc in self.at_tag.get(r[1], ()):
                sc.led.rm(i)
        for sc in self.at_tag.get(g, ()):
            self.settle(sc, i)

    def drop(self, i):
        r = self.rows.pop(i, None)
        if r is None:
            return
        self.view.take(r[1], r[0], i)
        for sc in self.at_tag.get(r[1], ()):
            sc.led.rm(i)

    def open(self, s, g, n, c):
        sc = Scroll(s, g, n, c)
        self.scrolls[s] = sc
        self.at_tag.setdefault(g, []).append(sc)

    # -- one page --------------------------------------------------------------------

    def page(self, s):
        sc = self.scrolls[s]
        gone = []
        left = sc.c

        while len(gone) < sc.n and left > 0:
            i = sc.led.front()
            if i is None:
                break
            w = self.rows[i][2]
            if w > left and gone:
                break
            sc.led.rm(i)
            sc.got.add(i)
            gone.append(i)
            left = left - w if w <= left else 0

        over = 0
        for pl in self.view.walk(sc.g, sc.mk):
            if len(gone) >= sc.n or left <= 0 or over >= sc.c:
                break
            i = pl[1]
            if i in sc.got:
                sc.mk = pl
                continue
            w = self.rows[i][2]
            if w <= left:
                sc.mk = pl
                sc.got.add(i)
                gone.append(i)
                left -= w
                continue
            if not gone:
                sc.mk = pl
                sc.got.add(i)
                gone.append(i)
                left = 0
                continue
            if self.standing() + w > self.hold:
                break
            sc.mk = pl
            sc.led.add(i, w)
            over += w

        parts = ["pg", str(s)]
        for i in gone:
            parts.append(str(i))
        self.out.append(" ".join(parts))

    # -- the closing report ------------------------------------------------------------

    def close(self):
        total = 0
        for s in sorted(self.scrolls):
            sc = self.scrolls[s]
            unseen = 0
            for i in self.view.members(sc.g):
                if i not in sc.got:
                    unseen += 1
            self.out.append("sc %d %d %d %d" % (s, len(sc.got), sc.led.count(), unseen))
            total += sc.led.tot
        self.out.append("tot %d" % total)


def run(text):
    run_ = None
    for raw in text.splitlines():
        f = raw.split()
        if not f:
            continue
        if f[0] == "cfg":
            run_ = Run(int(f[1]))
            continue
        a = [int(x) for x in f[1:]]
        if f[0] == "row" or f[0] == "add":
            run_.add(a[0], a[1], a[2], a[3])
        elif f[0] == "move":
            run_.move(a[0], a[1])
        elif f[0] == "tag":
            run_.retag(a[0], a[1])
        elif f[0] == "drop":
            run_.drop(a[0])
        elif f[0] == "open":
            run_.open(a[0], a[1], a[2], a[3])
        elif f[0] == "next":
            run_.page(a[0])
    run_.close()
    return run_.out


def expect(lines):
    return run("\n".join(lines) + "\n")
