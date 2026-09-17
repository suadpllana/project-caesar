"""The sealed model: what a program is supposed to print.

Written from the stated rules rather than from the service under test, and kept apart from it
on purpose. Where the contract leaves a structure free this makes the other choice: a record
is a two-slot list rather than an object, the records under one are found by walking every
record's chain of parents rather than from an index of children, the take-away builds a set of
positions rather than a surviving list, and the queue's own order is the only order kept - the
service is free to keep whatever else it likes.

The one structure both sides are forced into is carrying the laid-over view forward across the
changes the user makes and rebuilding it when the confirmed records or the queue move, because
the execution limit on the worker does not fit a rebuild per question. That is a limit on both
implementations, not a shared reading of the rules.

The rules it applies, one per block below:

  view      the confirmed records with the queue laid over them in the order the user made it
  lay       what one change does to a set of records, including doing nothing at all
  reach     the records under one, and the move that would put a record under itself
  hold      which changes may go out, and how one that stays behind holds later ones
  answer    which change an answer lands on, and what acceptance and refusal each do
  cancel    a removal of a record the server has never confirmed
  print     the four printed shapes and the order records come out in
"""


def expect(lines):
    return _Run(lines).go()


class _Run:
    def __init__(self, lines):
        self.lines = lines
        self.base = {}          # name -> [parent, {field: value}], in the order learnt
        self.q = []             # [kind, about, other, value, sent]
        self.sid = {}           # name -> the id the server gave it
        self.oid = set()        # names that arrived carrying an id
        self.nid = 0            # ids handed out so far
        self.out = []
        self.vw = None          # the laid-over view, carried forward where it can be

    # --- identity ---------------------------------------------------------------------

    def has_id(self, name):
        return name in self.sid or name in self.oid

    def show(self, name):
        return self.sid.get(name, name)

    # --- what a change names ----------------------------------------------------------

    @staticmethod
    def about(c):
        return c[1]

    @staticmethod
    def named(c):
        if c[0] in ("new", "mov") and c[2] != "-":
            return (c[1], c[2])
        return (c[1],)

    # --- reach ------------------------------------------------------------------------

    @staticmethod
    def owns(rec, top, name):
        """Is `name` `top` itself or somewhere under it, following parents upward."""
        at, steps = name, 0
        while at is not None:
            if at == top:
                return True
            row = rec.get(at)
            if row is None:
                return False
            at = row[0]
            steps += 1
            if steps > len(rec):
                return False
        return False

    # --- laying one change over a set of records --------------------------------------

    def lay(self, rec, c):
        kind, about, other, value = c[0], c[1], c[2], c[3]
        if kind == "new":
            if about in rec:
                return
            up = None if other == "-" else other
            if up is not None and up not in rec:
                return
            rec[about] = [up, {}]
        elif kind == "set":
            row = rec.get(about)
            if row is not None:
                row[1][other] = value
        elif kind == "add":
            row = rec.get(about)
            if row is not None:
                row[1][other] = row[1].get(other, 0) + value
        elif kind == "mov":
            row = rec.get(about)
            if row is None:
                return
            up = None if other == "-" else other
            if up is not None and up not in rec:
                return
            if up is not None and self.owns(rec, about, up):
                return
            row[0] = up
        elif kind == "cut":
            if about not in rec:
                return
            for name in [n for n in rec if self.owns(rec, about, n)]:
                del rec[name]

    # --- the view ---------------------------------------------------------------------

    def view(self):
        if self.vw is None:
            rec = {}
            for name, row in self.base.items():
                rec[name] = [row[0], dict(row[1])]
            for c in self.q:
                self.lay(rec, c)
            self.vw = rec
        return self.vw

    # --- the queue --------------------------------------------------------------------

    def take(self, c):
        if c[0] == "cut" and not self.has_id(c[1]):
            at = -1
            for i, q in enumerate(self.q):
                if q[0] == "new" and q[1] == c[1]:
                    at = i
                    break
            if at >= 0:
                seed = {self.about(self.q[at])}
                del self.q[at]
                self.sweep(at, seed)
                self.vw = None
                return
        self.q.append(c)
        if self.vw is not None:
            self.lay(self.vw, c)

    def sweep(self, at, seed):
        """Take away every later change naming a record that a taken change is about."""
        killed = []
        for i in range(at, len(self.q)):
            if seed.intersection(self.named(self.q[i])):
                seed.add(self.about(self.q[i]))
                killed.append(i)
        for i in reversed(killed):
            del self.q[i]
        return len(killed)

    def send(self):
        held = set()
        for c in self.q:
            if c[4]:
                continue
            names = self.named(c)
            wait = False
            for one in names:
                if c[0] == "new" and one == c[1]:
                    continue
                if not self.has_id(one):
                    wait = True
            if wait or held.intersection(names):
                held.add(self.about(c))
                continue
            c[4] = True
            self.out.append("out %s %s" % (c[0], self.show(c[1])))

    def answer(self, good):
        at = -1
        for i, c in enumerate(self.q):
            if c[4]:
                at = i
                break
        if at < 0:
            self.out.append("idle")
            return
        c = self.q.pop(at)
        if good:
            self.lay(self.base, c)
            if c[0] == "new":
                self.nid += 1
                self.sid[c[1]] = "s%d" % self.nid
            self.out.append("ack %s %s" % (c[0], self.show(c[1])))
        else:
            self.out.append("gone %d" % (1 + self.sweep(at, {self.about(c)})))
        self.vw = None

    def land(self, c):
        if c[0] == "new":
            self.oid.add(c[1])
        self.lay(self.base, c)
        self.vw = None

    # --- printing ---------------------------------------------------------------------

    def row(self, tag, name, record):
        up = "-" if record[0] is None else self.show(record[0])
        parts = [tag, self.show(name), up]
        for field in sorted(record[1]):
            parts.append("%s=%d" % (field, record[1][field]))
        self.out.append(" ".join(parts))

    # --- the program ------------------------------------------------------------------

    def go(self):
        for line in self.lines:
            bits = line.split()
            if not bits:
                continue
            self.one(bits)
        return self.out

    def one(self, bits):
        head = bits[0]
        if head == "new":
            self.take(["new", bits[1], bits[2], 0, False])
        elif head == "set":
            self.take(["set", bits[1], bits[2], int(bits[3]), False])
        elif head == "add":
            self.take(["add", bits[1], bits[2], int(bits[3]), False])
        elif head == "mov":
            self.take(["mov", bits[1], bits[2], 0, False])
        elif head == "cut":
            self.take(["cut", bits[1], "-", 0, False])
        elif head == "snd":
            self.send()
        elif head == "ok":
            self.answer(True)
        elif head == "no":
            self.answer(False)
        elif head == "oth":
            kind = bits[1]
            if kind in ("set", "add"):
                self.land([kind, bits[2], bits[3], int(bits[4]), False])
            elif kind in ("new", "mov"):
                self.land([kind, bits[2], bits[3], 0, False])
            elif kind == "cut":
                self.land([kind, bits[2], "-", 0, False])
        elif head == "ask":
            record = self.view().get(bits[1])
            if record is None:
                self.out.append("none")
            else:
                self.row("rec", bits[1], record)
        elif head == "all":
            for name, record in self.view().items():
                self.row("row", name, record)
