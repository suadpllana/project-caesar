from plan.keep import there
from plan.look import groups


class Node:
    def __init__(self):
        self.ok = True
        self.moved = False
        self.clean = True
        self.via_roll = False
        self.before = []
        self.computed = []
        self.line = None
        self.word = None


class Settler:
    def __init__(self, pp, hit):
        self.pp = pp
        self.hit = hit
        self.nodes = {}

    def stored(self, name, i):
        if (name, i) == self.pp.fix:
            return True, True
        if (name, i) not in self.hit or name not in self.pp.reads:
            return False, True
        n = self.nodes[(name, i)]
        return (True, n.clean) if n.line == "run" else (False, False)

    def wants(self, name, i):
        """Partitions whose nodes must exist before (name, i) can be settled."""
        pp = self.pp
        out = []
        for roll, src, parts in groups(pp, name, i):
            if roll is not None and there(pp, roll, i) and (roll, i) in self.hit:
                out.append((roll, i))
            for p in parts:
                if there(pp, src, p):
                    if (src, p) in self.hit and src in pp.reads:
                        out.append((src, p))
                elif src in pp.reads:
                    out.append((src, p))
        return out

    def ensure(self, key):
        stack = [(key, False)]
        while stack:
            k, expanded = stack.pop()
            if k in self.nodes:
                continue
            if not expanded:
                stack.append((k, True))
                for w in self.wants(*k):
                    if w not in self.nodes:
                        stack.append((w, False))
            else:
                self.nodes[k] = self.build(*k)

    def build(self, name, i):
        pp = self.pp
        n = Node()
        exists = there(pp, name, i)
        if exists and (name, i) in pp.pins:
            n.line, n.word, n.clean = "hold", "pinned", False
            return n
        for roll, src, parts in groups(pp, name, i):
            if roll is not None and there(pp, roll, i):
                moved, clean = self.stored(roll, i)
                if clean:
                    n.via_roll = True
                    n.moved = n.moved or moved
                    if moved:
                        n.before.append((roll, i))
                    continue
            for p in parts:
                if there(pp, src, p):
                    moved, clean = self.stored(src, p)
                    n.moved = n.moved or moved
                    n.clean = n.clean and clean
                    if moved and (src, p) != pp.fix:
                        n.before.append((src, p))
                elif src not in pp.reads:
                    n.ok = False
                else:
                    t = self.nodes[(src, p)]
                    if not t.ok:
                        n.ok = False
                        continue
                    n.moved = n.moved or t.moved
                    n.clean = n.clean and t.clean
                    n.before.append((src, p))
                    n.computed.append((src, p))
        if not exists:
            n.line = "temp"
        elif not n.ok:
            n.line, n.word = "hold", "lost"
        elif not n.moved:
            n.line, n.word = "hold", "same"
        else:
            n.line = "run"
            n.word = "part" if not n.clean else ("sub" if n.via_roll else "full")
        return n


def settle(pp, hit):
    s = Settler(pp, hit)
    mine = [k for k in hit if k[0] in pp.reads and there(pp, *k)]
    for k in mine:
        s.ensure(k)
    runs = [k for k in mine if s.nodes[k].line == "run"]
    holds = [k for k in mine if s.nodes[k].line == "hold"]
    out = set(runs)
    stack = list(runs)
    while stack:
        for t in s.nodes[stack.pop()].computed:
            if t not in out:
                out.add(t)
                stack.append(t)
    return s, out, holds
