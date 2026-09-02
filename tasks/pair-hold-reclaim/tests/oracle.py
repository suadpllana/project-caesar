"""A second implementation of the reclamation specification, written from the
specification rather than from the tree, and sharing no code with it.

It exists to prove that what the verifier grades is the specification and not one
author's arrangement of it. The store here is a handful of plain dictionaries rather
than cell objects; reach is naive Kleene iteration over the whole relation rather than
a worklist alternating with table sweeps; the pass is a small state machine over an
explicit round counter rather than a loop with a break. Where the two agree on every
row of several thousand streams, the rows are a property of the rules.

The specification, in the order the pass applies it:

  reach            The bound names are the seeds. A link puts its target in reach
                   whenever its holder is. A one-key entry puts its value in reach while
                   its key is; a two-key entry while both of its keys are. The answer is
                   the least set closed under all three.

  round            Mark. Empty every plain watch whose cell that marking put out of
                   reach, oldest watch first. Choose the pending cleanups the round may
                   run: a cell no other pending cell can reach, where "can reach" is the
                   same operator seeded with the held cells and the rest of the pending
                   set. If every pending cell is reachable from another, the oldest goes
                   alone. Run them, oldest first, each landing its action immediately.

  settle           Rounds repeat until a marking leaves no cleanup to run. That marking,
                   and no earlier one, decides what goes.

  let go           Oldest first: empty whatever watches still name the cell, then remove
                   it, dropping every entry either of whose cells it is.
"""

PLAIN = "plain"
ACT_HEADS = ("bind", "unbind", "edge", "cut", "pair", "both", "look", "none")


class Model:
    def __init__(self):
        self.seq = []
        self.link = {}
        self.root = {}
        self.one = []
        self.two = []
        self.wname = []
        self.wkind = {}
        self.wtgt = {}
        self.woff = {}
        self.act = {}
        self.ran = set()
        self.rows = []
        self.pn = 0

    def row(self, code, rest):
        self.rows.append("%d %s %s" % (self.pn, code, rest))

    def alive(self, i):
        return i in self.seq

    def mk(self, i):
        if i not in self.seq:
            self.seq.append(i)
            self.link[i] = []

    def bind(self, nm, i):
        if self.alive(i):
            self.root[nm] = i

    def unbind(self, nm):
        self.root.pop(nm, None)

    def edge(self, a, b):
        if self.alive(a) and self.alive(b) and b not in self.link[a]:
            self.link[a].append(b)

    def cut(self, a, b):
        if self.alive(a) and b in self.link[a]:
            self.link[a].remove(b)

    def one_add(self, k, v):
        if self.alive(k) and self.alive(v) and (k, v) not in self.one:
            self.one.append((k, v))

    def two_add(self, a, b, v):
        if self.alive(a) and self.alive(b) and self.alive(v) and (a, b, v) not in self.two:
            self.two.append((a, b, v))

    def see(self, nm, kd, i):
        if nm in self.wkind or not self.alive(i):
            return
        self.wname.append(nm)
        self.wkind[nm] = kd
        self.wtgt[nm] = i
        self.woff[nm] = False

    def arm(self, i, act):
        if self.alive(i) and i not in self.act:
            self.act[i] = act

    def look(self, nm):
        if nm not in self.wkind:
            self.row("sh", "%s ?" % nm)
        elif self.woff[nm]:
            self.row("sh", "%s -" % nm)
        else:
            self.row("sh", "%s %d" % (nm, self.wtgt[nm]))

    def held(self):
        return [i for i in self.root.values() if self.alive(i)]

    def pending(self, i):
        return i in self.act and i not in self.ran

    def reach(self, seeds):
        live = set(i for i in seeds if self.alive(i))
        moving = True
        while moving:
            moving = False
            for i in sorted(live):
                for j in self.link.get(i, []):
                    if j not in live:
                        live.add(j)
                        moving = True
            for k, v in self.one:
                if k in live and v not in live:
                    live.add(v)
                    moving = True
            for a, b, v in self.two:
                if a in live and b in live and v not in live:
                    live.add(v)
                    moving = True
        return live

    def wipe(self, nm):
        if not self.woff[nm]:
            self.woff[nm] = True
            self.row("em", nm)

    def fire(self, i):
        self.ran.add(i)
        self.row("cn", str(i))
        a = self.act[i]
        head = a[0]
        if head == "bind":
            self.bind(a[1], int(a[2]))
        elif head == "unbind":
            self.unbind(a[1])
        elif head == "edge":
            self.edge(int(a[1]), int(a[2]))
        elif head == "cut":
            self.cut(int(a[1]), int(a[2]))
        elif head == "pair":
            self.one_add(int(a[1]), int(a[2]))
        elif head == "both":
            self.two_add(int(a[1]), int(a[2]), int(a[3]))
        elif head == "look":
            self.look(a[1])

    def letgo(self, i):
        for nm in self.wname:
            if self.wtgt[nm] == i:
                self.wipe(nm)
        for k, v in list(self.one):
            if i in (k, v):
                self.one.remove((k, v))
                self.row("dp", "%d %d" % (k, v))
        for a, b, v in list(self.two):
            if i in (a, b, v):
                self.two.remove((a, b, v))
                self.row("db", "%d %d %d" % (a, b, v))
        self.seq.remove(i)
        del self.link[i]
        for d in self.seq:
            if i in self.link[d]:
                self.link[d].remove(i)
        self.row("rl", str(i))

    def choose(self, gone):
        pend = [i for i in gone if self.pending(i)]
        if not pend:
            return []
        base = self.held()
        picked = []
        for i in pend:
            rest = base + [j for j in pend if j != i]
            if i not in self.reach(rest):
                picked.append(i)
        return picked if picked else [pend[0]]

    def sweep(self):
        self.pn += 1
        gone = []
        rounds = 0
        while True:
            rounds += 1
            if rounds > len(self.seq) + 2:
                raise RuntimeError("pass did not settle")
            live = self.reach(self.held())
            gone = [i for i in self.seq if i not in live]
            spent = set(gone)
            for nm in self.wname:
                if self.wkind[nm] == PLAIN and not self.woff[nm] and self.wtgt[nm] in spent:
                    self.wipe(nm)
            go = self.choose(gone)
            if not go:
                break
            for i in go:
                self.fire(i)
        for i in list(gone):
            self.letgo(i)


def read(text):
    ops = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        f = line.split()
        if f[0] == "new":
            ops.append(("new", int(f[1])))
        elif f[0] in ("edge", "cut", "pair"):
            ops.append((f[0], int(f[1]), int(f[2])))
        elif f[0] == "both":
            ops.append(("both", int(f[1]), int(f[2]), int(f[3])))
        elif f[0] == "bind":
            ops.append(("bind", f[1], int(f[2])))
        elif f[0] in ("unbind", "show"):
            ops.append((f[0], f[1]))
        elif f[0] == "watch":
            ops.append(("watch", f[1], f[2], int(f[3])))
        elif f[0] == "arm":
            body = tuple(f[2:])
            if not body or body[0] not in ACT_HEADS:
                raise ValueError(line)
            ops.append(("arm", int(f[1]), body))
        elif f[0] == "pass":
            ops.append(("pass",))
        else:
            raise ValueError(line)
    return ops


def state(m):
    out = []
    for i in m.seq:
        out.append("c %d %s" % (i, ",".join(str(x) for x in m.link[i])))
    for k, v in m.one:
        out.append("p %d %d" % (k, v))
    for a, b, v in m.two:
        out.append("b %d %d %d" % (a, b, v))
    for nm in m.wname:
        out.append("w %s %s %s" % (nm, m.wkind[nm], "-" if m.woff[nm] else str(m.wtgt[nm])))
    for nm in sorted(m.root):
        out.append("r %s %d" % (nm, m.root[nm]))
    return out


def play(text):
    m = Model()
    for op in read(text):
        h = op[0]
        if h == "new":
            m.mk(op[1])
        elif h == "edge":
            m.edge(op[1], op[2])
        elif h == "cut":
            m.cut(op[1], op[2])
        elif h == "pair":
            m.one_add(op[1], op[2])
        elif h == "both":
            m.two_add(op[1], op[2], op[3])
        elif h == "bind":
            m.bind(op[1], op[2])
        elif h == "unbind":
            m.unbind(op[1])
        elif h == "watch":
            m.see(op[1], op[2], op[3])
        elif h == "arm":
            m.arm(op[1], op[2])
        elif h == "show":
            m.look(op[1])
        elif h == "pass":
            m.sweep()
    return {"log": list(m.rows), "state": state(m)}
