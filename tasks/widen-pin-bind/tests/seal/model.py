"""The binder, written a second time and apart from the reference, as the definition of correct.

Nothing here is shared with `/app`: the program text is parsed again, the rise distances come
from a closure computed once over the whole graph rather than a search per question, the
survivors of a call are reduced by elimination instead of each being checked against all the
others, and the pins are carried as a frozen set of pairs rather than a copied map. Where the
two implementations agree they agree because the rules say so.

The rules, in the order a call meets them:

  1  a kind rises to another over the shortest chain of declared edges; a kind rises to itself
     in no steps
  2  the candidates of a call are the entries carrying its name that take as many slots as it
     has arguments
  3  an open entry that is not pinned settles first: its open slots are bound asking for
     nothing, and the entry settles at the single least kind all of them rise to
  4  a settled kind that does not rise to the entry's bound drops the candidate
  5  every other slot asks for its declared kind, an open slot of a pinned entry asks for the
     pinned kind, and a call in a slot is bound asking for that kind
  6  a slot costs the steps from the kind its argument stands at to the kind the slot asks for,
     and an argument that does not rise there drops the candidate
  7  the last cost is the steps from the kind the entry gives back to the kind the call was
     asked for, nothing when it was asked for nothing, and no rise there drops the candidate
  8  the winner is the candidate no worse at every cost than each other survivor and better at
     one; with none such the call is ambiguous, and with no survivor at all it has no binding
  9  the winner's pins are kept in the order they were made, the open slots of an unpinned
     entry having been bound before its other slots, and its own pin last; every other trial's
     pins are dropped
 10  a kept call adds every cost of its vector to the tally
"""
import re

WORD = re.compile(r"[a-z][a-z0-9]*|[(),*]")


class Call:
    __slots__ = ("name", "args", "site")

    def __init__(self, name, args, site):
        self.name = name
        self.args = args
        self.site = site


def read(lines):
    """Kinds, rise edges, entries, values and expressions, in declaration order."""
    kinds, up, ents, vals, asks = [], {}, [], {}, []
    for raw in lines:
        row = raw.strip()
        if not row:
            continue
        bits = row.split()
        tag = bits[0]
        if tag == "kind":
            kinds.append(bits[1])
            up[bits[1]] = []
        elif tag == "rise":
            up[bits[1]].append(bits[2])
        elif tag == "entry":
            ents.append({"name": bits[1], "open": False, "bound": None,
                         "ret": bits[2], "par": bits[3:]})
        elif tag == "open":
            ents.append({"name": bits[1], "open": True, "bound": bits[2],
                         "ret": bits[3], "par": bits[4:]})
        elif tag == "val":
            vals[bits[1]] = bits[2]
        elif tag == "ask":
            asks.append(tree(row.split(None, 1)[1]))
        else:
            raise ValueError(row)
    return kinds, up, ents, vals, asks


def tree(text):
    """An expression, with its calls numbered outermost first, left to right."""
    toks = WORD.findall(text)
    box = {"at": 0, "n": 0}

    def take():
        name = toks[box["at"]]
        box["at"] += 1
        if box["at"] < len(toks) and toks[box["at"]] == "(":
            mine = box["n"]
            box["n"] += 1
            box["at"] += 1
            kids = [take()]
            while toks[box["at"]] == ",":
                box["at"] += 1
                kids.append(take())
            box["at"] += 1
            return Call(name, kids, mine)
        return Call(name, None, None)

    return take()


def closure(kinds, up):
    """Steps between every ordered pair, by repeated relaxation over the whole graph."""
    far = {}
    for k in kinds:
        far[(k, k)] = 0
    for k in kinds:
        for nxt in up.get(k, ()):
            if far.get((k, nxt), 99) > 1:
                far[(k, nxt)] = 1
    moved = True
    while moved:
        moved = False
        for (a, b), d in list(far.items()):
            for c in up.get(b, ()):
                if far.get((a, c), 99) > d + 1:
                    far[(a, c)] = d + 1
                    moved = True
    return far


def front(vecs):
    """The one vector that beats every other survivor, by elimination; None when none does."""
    live = list(range(len(vecs)))
    for i in list(live):
        for j in range(len(vecs)):
            if i == j:
                continue
            a, b = vecs[i], vecs[j]
            better = False
            worse = False
            for x, y in zip(a, b):
                if x < y:
                    better = True
                if x > y:
                    worse = True
            if worse or not better:
                if i in live:
                    live.remove(i)
                break
    return live[0] if len(live) == 1 else None


class Run:
    def __init__(self, lines):
        self.kinds, self.up, self.ents, self.vals, self.asks = read(lines)
        self.far = closure(self.kinds, self.up)
        self.seen = {}
        self.tally = 0
        self.pins = frozenset()

    def steps(self, a, b):
        return self.far.get((a, b))

    def settle(self, sources):
        over = [k for k in self.kinds
                if all(self.steps(s, k) is not None for s in sources)]
        least = [k for k in over
                 if all(self.steps(k, other) is not None for other in over)]
        return least[0] if len(least) == 1 else None

    def call(self, node, want, pins):
        key = (id(node), want, pins)
        if key in self.seen:
            return self.seen[key]
        rows = []
        for idx, ent in enumerate(self.ents):
            if ent["name"] != node.name or len(ent["par"]) != len(node.args):
                continue
            got = self.try_one(node, idx, ent, want, pins)
            if got is not None:
                rows.append(got)
        if not rows:
            out = ("none", None, [], [], 0)
        else:
            which = front([row[0] for row in rows])
            if which is None:
                out = ("amb", None, [], [], 0)
            else:
                vec, kind, binds, made, deep = rows[which]
                out = ("bind", kind, binds, made, deep + sum(vec))
        self.seen[key] = out
        return out

    def try_one(self, node, idx, ent, want, pins):
        held = dict(pins)
        cost = [None] * len(node.args)
        under = [[] for _ in node.args]
        made = []
        deep = 0
        fixed = held.get(idx) if ent["open"] else None
        mine = None
        if ent["open"] and fixed is None:
            spots = [i for i, p in enumerate(ent["par"]) if p == "*"]
            if not spots:
                return None
            stands = []
            for i in spots:
                arg = node.args[i]
                if arg.args is None:
                    stands.append(self.vals[arg.name])
                    continue
                how, kind, binds, pinned, sub = self.call(arg, None, frozenset(held.items()))
                if how != "bind":
                    return None
                held.update(pinned)
                made += pinned
                under[i] = binds
                deep += sub
                stands.append(kind)
            fixed = self.settle(stands)
            if fixed is None or self.steps(fixed, ent["bound"]) is None:
                return None
            for i, was in zip(spots, stands):
                cost[i] = self.steps(was, fixed)
            mine = (idx, fixed)
        for i, par in enumerate(ent["par"]):
            if cost[i] is not None:
                continue
            asks = fixed if par == "*" else par
            arg = node.args[i]
            if arg.args is None:
                step = self.steps(self.vals[arg.name], asks)
            else:
                how, kind, binds, pinned, sub = self.call(arg, asks, frozenset(held.items()))
                if how != "bind":
                    return None
                held.update(pinned)
                made += pinned
                under[i] = binds
                deep += sub
                step = self.steps(kind, asks)
            if step is None:
                return None
            cost[i] = step
        gives = fixed if ent["ret"] == "*" else ent["ret"]
        last = 0 if want is None else self.steps(gives, want)
        if last is None:
            return None
        if mine is not None:
            made = made + [mine]
        binds = [(node.site, idx)]
        for part in under:
            binds += part
        return (cost + [last], gives, binds, made, deep)


def expect(lines):
    """Every line the binder prints for this program."""
    run = Run(lines)
    out = []
    for k, node in enumerate(run.asks):
        how, kind, binds, made, deep = run.call(node, None, run.pins)
        if how != "bind":
            out.append("res %d %s" % (k, how))
            continue
        held = dict(run.pins)
        held.update(made)
        run.pins = frozenset(held.items())
        run.tally += deep
        for site, idx in binds:
            out.append("bind %d %d %d" % (k, site, idx))
        for idx, kind2 in made:
            out.append("pin %d %s" % (idx, kind2))
        out.append("res %d %s" % (k, kind))
    out.append("tally %d" % run.tally)
    return out
