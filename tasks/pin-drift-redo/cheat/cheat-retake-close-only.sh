#!/bin/bash
# a key that has moved is taken again only when the transaction closes
set -euo pipefail

cat > /app/led/ver.py <<'PYEOF'
class Store:
    def __init__(self):
        self.val = {}

    def open(self, wide):
        self.val = {}
        for k in range(wide):
            self.val[k] = 0

    def at(self, k):
        return self.val[k]

    def write(self, keys, held):
        pairs = []
        for k in sorted(keys):
            pairs.append((k, held[k]))
        for k, v in pairs:
            self.val[k] = v
        return pairs
PYEOF

cat > /app/led/take.py <<'PYEOF'
NAMED = {
    "rd": (2,),
    "put": (2,),
    "add": (2,),
    "cpy": (2, 3),
    "raw": (2, 3),
    "chk": (2,),
    "lim": (2,),
}


def names(op):
    if op[0] == "bmp":
        return tuple(range(op[2], op[3]))
    where = NAMED.get(op[0])
    if where is None:
        return ()
    return tuple(op[i] for i in where)


class Taken:
    def __init__(self):
        self.num = {}

    def see(self, store, keys):
        fresh = []
        for k in keys:
            standing = store.at(k)
            if k not in self.num:
                self.num[k] = standing
                fresh.append(k)
            elif self.num[k] != standing:
                pass
        return fresh

    def again(self, store):
        for k in self.num:
            standing = store.at(k)
            if self.num[k] != standing:
                self.num[k] = standing

    def at(self, k):
        return self.num[k]

    def keys(self):
        return list(self.num)
PYEOF

cat > /app/led/hold.py <<'PYEOF'
OWED = 0
SET = 1


class Held:
    def __init__(self):
        self.form = {}

    def start(self, keys):
        for k in keys:
            self.form[k] = (OWED, k, 0)

    def at(self, k, taken):
        kind, one, two = self.form[k]
        if kind == SET:
            return one
        return taken.at(one) + two

    def put(self, k, n):
        self.form[k] = (SET, n, 0)

    def add(self, k, n):
        kind, one, two = self.form[k]
        if kind == SET:
            self.form[k] = (SET, one + n, 0)
        else:
            self.form[k] = (OWED, one, two + n)

    def copy(self, k, j):
        self.form[k] = self.form[j]

    def raw(self, k, j):
        self.form[k] = (OWED, j, 0)

    def stick(self, k, v):
        self.form[k] = (SET, v, 0)

    def save(self):
        return dict(self.form)

    def back(self, saved, keys):
        form = {}
        for k in keys:
            was = saved.get(k)
            form[k] = was if was is not None else (OWED, k, 0)
        self.form = form
PYEOF

cat > /app/led/work.py <<'PYEOF'
from led import hold
from led import take


class Txn:
    def __init__(self, num):
        self.num = num
        self.taken = take.Taken()
        self.held = hold.Held()
        self.ents = []
        self.marks = []
        self.wrote = set()

    def see(self, store, keys):
        self.held.start(self.taken.see(store, keys))

    def note(self, ent):
        self.ents.append(ent)

    def sets(self, k, ent):
        self.ents.append(ent)
        self.wrote.add(k)

    def mark(self):
        self.marks.append((len(self.ents), self.held.save(), set(self.wrote)))
        self.ents.append(("m",))

    def cut(self):
        if self.marks:
            back, form, wrote = self.marks.pop()
            del self.ents[back:]
            self.wrote = wrote
        else:
            self.ents = []
            form = {}
            self.wrote = set()
        self.held.back(form, self.taken.keys())
PYEOF

cat > /app/led/step.py <<'PYEOF'
from led import close
from led import say
from led import take
from led import work


def one(store, box, op, out):
    kind = op[0]
    if kind == "cfg":
        store.open(op[1])
        return
    if kind == "tx":
        box[op[1]] = work.Txn(op[1])
        return
    t = box[op[1]]
    t.see(store, take.names(op))
    if kind == "rd":
        k = op[2]
        v = t.held.at(k, t.taken)
        out.append(say.read(t.num, k, v))
        t.note(("f", k, v))
        t.held.stick(k, v)
    elif kind == "put":
        k = op[2]
        t.sets(k, ("p", k, op[3]))
        t.held.put(k, op[3])
    elif kind == "add":
        k = op[2]
        t.sets(k, ("a", k, op[3]))
        t.held.add(k, op[3])
    elif kind == "cpy":
        k = op[2]
        t.sets(k, ("c", k, op[3]))
        t.held.copy(k, op[3])
    elif kind == "raw":
        k = op[2]
        t.sets(k, ("r", k, op[3]))
        t.held.raw(k, op[3])
    elif kind == "bmp":
        for k in range(op[2], op[3]):
            t.sets(k, ("a", k, op[4]))
            t.held.add(k, op[4])
    elif kind == "chk":
        t.note(("k", op[2], op[3]))
    elif kind == "lim":
        t.note(("l", op[2], op[3]))
    elif kind == "mk":
        t.mark()
    elif kind == "un":
        t.cut()
    elif kind == "drp":
        del box[op[1]]
    elif kind == "fin":
        out.append(close.shut(store, t))
        del box[op[1]]
PYEOF

cat > /app/led/close.py <<'PYEOF'
from led import say


def shut(store, t):
    t.taken.again(store)
    base = {}
    for k in t.taken.keys():
        base[k] = t.taken.at(k)
    held = dict(base)
    wrote = set()
    stack = []
    for ent in t.ents:
        kind = ent[0]
        if kind == "p":
            held[ent[1]] = ent[2]
            wrote.add(ent[1])
        elif kind == "a":
            held[ent[1]] = held[ent[1]] + ent[2]
            wrote.add(ent[1])
        elif kind == "c":
            held[ent[1]] = held[ent[2]]
            wrote.add(ent[1])
        elif kind == "r":
            held[ent[1]] = base[ent[2]]
            wrote.add(ent[1])
        elif kind == "f":
            held[ent[1]] = ent[2]
        elif kind == "m":
            stack.append((dict(held), set(wrote)))
        elif kind == "k" or kind == "l":
            got = held[ent[1]]
            if kind == "k":
                stands = got == ent[2]
            else:
                stands = got >= ent[2]
            if not stands:
                if not stack:
                    return say.shut_no(t.num)
                held, wrote = stack.pop()
    return say.shut_ok(t.num, store.write(wrote, held))
PYEOF
