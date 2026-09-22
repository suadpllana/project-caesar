"""The specification of heard-cut-revoice, encoded as directly as it can be.

Authoring only; never ships. Everything is recomputed from scratch on every tick - the whole
page walked for exposure and regions, every key compared, every waiting difference rescanned
at every selection - so this is the slow, obviously-faithful reading of the model in
tasks/heard-cut-revoice/STATE.md. It owns its own tree and parser so that a defect in the
shipped page model cannot hide inside it. The sealed model and the reference are both checked
against it on small and medium pages; it is also the "naive but correct" family whose timing
the resource gate is measured against.
"""
import sys

POL = ("polite", "assertive")


class Tree:
    def __init__(self):
        self.par = {0: None}
        self.kid = {0: []}
        self.att = {0: {}}
        self.txt = {}

    def put(self, n, p, pos):
        ks = self.kid[p]
        ks.insert(len(ks) if pos is None else pos, n)
        self.par[n] = p

    def apply(self, op):
        head = op[0]
        if head == "add":
            _, n, p, pos, kind, val = op
            if kind == "el":
                self.kid[n] = []
                self.att[n] = {}
            else:
                self.txt[n] = val
            self.put(n, p, pos)
        elif head == "move":
            _, n, p, pos = op
            self.kid[self.par[n]].remove(n)
            self.put(n, p, pos)
        elif head == "drop":
            _, n = op
            self.kid[self.par[n]].remove(n)
            self.par[n] = None
        elif head == "text":
            self.txt[op[1]] = op[2]
        elif head == "set":
            self.att[op[1]][op[2]] = op[3]
        else:
            self.att[op[1]].pop(op[2], None)

    def hides(self, e):
        a = self.att[e]
        return "hidden" in a or a.get("aria-hidden") == "true"

    def exposed(self, n):
        x = n
        while x is not None:
            if x not in self.txt and self.hides(x):
                return False
            if x == 0:
                return True
            x = self.par[x]
        return False

    def region(self, n):
        x = n
        while x is not None:
            if x not in self.txt and "aria-live" in self.att[x]:
                return x
            x = self.par[x]
        return None

    def voicing(self, r):
        return self.exposed(r) and self.att[r].get("aria-live") in POL

    def relevant(self, r):
        got = set()
        for tok in self.att[r].get("aria-relevant", "").split():
            if tok == "all":
                got |= {"additions", "removals", "text"}
            elif tok in ("additions", "removals", "text"):
                got.add(tok)
        return got or {"additions", "text"}

    def current(self):
        out = {}
        todo = [(0, None)]
        while todo:
            x, r = todo.pop()
            if x in self.txt:
                if r is not None:
                    out[(r, x)] = (self.txt[x], self.par[x])
                continue
            if self.hides(x):
                continue
            if "aria-live" in self.att[x]:
                r = x
            for k in reversed(self.kid[x]):
                todo.append((k, r))
        return out

    def text_of(self, u):
        words = []
        todo = [u]
        while todo:
            x = todo.pop()
            if x in self.txt:
                words.append(self.txt[x])
                continue
            if self.hides(x):
                continue
            todo.extend(reversed(self.kid[x]))
        return " ".join(words)


def parse(text):
    last, ticks, cur = None, {}, None
    for raw in text.splitlines():
        p = raw.split()
        if not p:
            continue
        if p[0] == "page":
            last = int(p[1])
        elif p[0].startswith("@"):
            cur = int(p[0][1:])
            ticks[cur] = []
        elif p[0] == "add":
            pos = None if p[3] == "end" else int(p[3])
            val = p[5] if p[4] == "el" else " ".join(p[5:])
            ticks[cur].append(("add", int(p[1]), int(p[2]), pos, p[4], val))
        elif p[0] == "move":
            ticks[cur].append(("move", int(p[1]), int(p[2]), None if p[3] == "end" else int(p[3])))
        elif p[0] == "drop":
            ticks[cur].append(("drop", int(p[1])))
        elif p[0] == "text":
            ticks[cur].append(("text", int(p[1]), " ".join(p[2:])))
        elif p[0] == "set":
            ticks[cur].append(("set", int(p[1]), p[2], " ".join(p[3:])))
        elif p[0] == "unset":
            ticks[cur].append(("unset", int(p[1]), p[2]))
        else:
            raise ValueError(raw)
    return last, ticks


def differs(c, e):
    if (c is None) != (e is None):
        return True
    return c is not None and c[0] != e[0]


def kind(c, e):
    if e is None:
        return "additions"
    if c is None:
        return "removals"
    return "text"


class Play:
    def __init__(self, pol, fin, carried):
        self.pol = pol
        self.fin = fin
        self.carried = carried


def run(text):
    last, ticks = parse(text)
    tr = Tree()
    for op in ticks[0]:
        tr.apply(op)
    belief = dict(tr.current())
    ages = {}
    play = None
    log = []

    def expected():
        e = dict(belief)
        if play is not None:
            for k, (v, _a) in play.carried.items():
                if v is None:
                    e.pop(k, None)
                else:
                    e[k] = v
        return e

    def absorb(k, c):
        if c is None:
            belief.pop(k, None)
        else:
            belief[k] = c
        if play is not None:
            play.carried.pop(k, None)

    def path(k, cur, exp):
        r, _n = k
        c = cur.get(k)
        if c is not None:
            s = c[1]
        else:
            a = exp[k][1]
            s = a if tr.exposed(a) and tr.region(a) == r else None
        if s is None:
            return [r]
        out = []
        x = s
        while True:
            out.append(x)
            if x == r:
                return out
            x = tr.par[x]

    def held(k, cur, exp):
        return any(tr.att[x].get("aria-busy") == "true" for x in path(k, cur, exp))

    def unit(k, cur, exp):
        r, _n = k
        c = cur.get(k)
        if c is not None:
            s = c[1]
        else:
            a = exp[k][1]
            if not (tr.exposed(a) and tr.region(a) == r):
                return None
            s = a
        x = s
        while True:
            v = tr.att[x].get("aria-atomic")
            if v == "true":
                return x
            if v == "false" or x == r:
                return None
            x = tr.par[x]

    def cls(k):
        return tr.att[k[0]]["aria-live"]

    for t in range(1, last + 1):
        for op in ticks.get(t, ()):
            tr.apply(op)

        if play is not None and play.fin == t:
            for k, (v, _a) in play.carried.items():
                if v is None:
                    belief.pop(k, None)
                else:
                    belief[k] = v
            play = None

        cur = tr.current()
        exp = expected()
        fresh = {}
        for k in set(cur) | set(exp):
            c, e = cur.get(k), exp.get(k)
            if not differs(c, e):
                continue
            r = k[0]
            if not tr.voicing(r) or kind(c, e) not in tr.relevant(r):
                absorb(k, c)
                continue
            fresh[k] = ages.get(k, t)
        ages = fresh

        if play is not None and play.pol == "polite":
            exp = expected()
            if any(cls(k) == "assertive" and not held(k, cur, exp) for k in ages):
                log.append("%d cut" % t)
                back = play.carried
                play = None
                for k, (_v, a) in back.items():
                    c, b = cur.get(k), belief.get(k)
                    if not differs(c, b):
                        ages.pop(k, None)
                        continue
                    r = k[0]
                    if not tr.voicing(r) or kind(c, b) not in tr.relevant(r):
                        absorb(k, c)
                        ages.pop(k, None)
                        continue
                    ages[k] = a

        while play is None:
            exp = expected()
            pend = [k for k in ages if not held(k, cur, exp)]
            if not pend:
                break
            loud = [k for k in pend if cls(k) == "assertive"]
            pool = loud or pend
            k0 = min(pool, key=lambda k: (ages[k], k[1], k[0]))
            u = unit(k0, cur, exp)
            if u is not None:
                group = [k for k in pool if unit(k, cur, exp) == u]
                words = tr.text_of(u)
            else:
                group = [k0]
                c = cur.get(k0)
                words = c[0] if c is not None else "removed " + exp[k0][0]
            carried = {k: (cur.get(k), ages[k]) for k in group}
            for k in group:
                del ages[k]
            if not words:
                for k, (v, _a) in carried.items():
                    if v is None:
                        belief.pop(k, None)
                    else:
                        belief[k] = v
                continue
            pol = cls(k0)
            play = Play(pol, t + len(words.split(" ")), carried)
            log.append("%d %s %s" % (t, pol, words))
    return log


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as fh:
        for line in run(fh.read()):
            print(line)
