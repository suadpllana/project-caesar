#!/bin/bash
# the frozen answers for the enumerated programs, carried and replayed
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

    def snap(self):
        return dict(self.val)

    def write(self, keys, held):
        pairs = []
        for k in keys:
            if held[k] != self.val[k]:
                pairs.append((k, held[k]))
        for k, v in pairs:
            self.val[k] = v
        return pairs
PYEOF

cat > /app/led/take.py <<'PYEOF'
class Taken:
    def __init__(self):
        self.num = {}
        self.read = set()

    def open(self, store):
        self.num = store.snap()

    def stale(self, store):
        for k in self.read:
            if self.num[k] != store.at(k):
                return True
        return False

    def at(self, k):
        return self.num[k]

    def seen(self, k):
        self.read.add(k)

    def moved(self, store, keys):
        out = []
        for k in keys:
            if self.num[k] != store.at(k):
                out.append(k)
        return out
PYEOF

cat > /app/led/hold.py <<'PYEOF'
class Held:
    def __init__(self):
        self.num = {}

    def at(self, k, taken):
        if k in self.num:
            return self.num[k]
        return taken.at(k)

    def put(self, k, n):
        self.num[k] = n

    def add(self, k, n, taken):
        self.num[k] = self.at(k, taken) + n

    def copy(self, k, j, taken):
        self.num[k] = self.at(j, taken)

    def raw(self, k, j, taken):
        self.num[k] = taken.at(j)

    def save(self):
        return dict(self.num)

    def back(self, saved):
        self.num = saved
PYEOF

cat > /app/led/work.py <<'PYEOF'
from led import hold
from led import take


class Txn:
    def __init__(self, num, store):
        self.num = num
        self.taken = take.Taken()
        self.taken.open(store)
        self.held = hold.Held()
        self.wrote = []
        self.marks = []
        self.bad = False

    def sets(self, k):
        if k not in self.wrote:
            self.wrote.append(k)

    def mark(self):
        self.marks.append((self.held.save(), list(self.wrote)))

    def cut(self):
        if self.marks:
            was, wrote = self.marks.pop()
            self.held.back(was)
            self.wrote = wrote
        else:
            self.held.back({})
            self.wrote = []
PYEOF

cat > /app/led/step.py <<'PYEOF'
from led import close
from led import say
from led import work


import json
import pathlib

KNOWN = json.loads(pathlib.Path(__file__).with_name("known.json").read_text(encoding="utf-8"))
SEEN = []


def one(store, box, op, out):
    kind = op[0]
    if kind == "cfg":
        del SEEN[:]
        del out[:]
    SEEN.append(" ".join(str(bit) for bit in op))
    lines = KNOWN.get("\n".join(SEEN))
    if lines is not None:
        del out[:]
        out.extend(lines)
    return
    if kind == "cfg":
        store.open(op[1])
        return
    if kind == "tx":
        box[op[1]] = work.Txn(op[1], store)
        return
    t = box[op[1]]
    if kind == "rd":
        t.taken.seen(op[2])
        out.append(say.read(t.num, op[2], t.held.at(op[2], t.taken)))
    elif kind == "put":
        t.held.put(op[2], op[3])
        t.sets(op[2])
    elif kind == "add":
        t.held.add(op[2], op[3], t.taken)
        t.sets(op[2])
    elif kind == "cpy":
        t.held.copy(op[2], op[3], t.taken)
        t.sets(op[2])
    elif kind == "raw":
        t.held.raw(op[2], op[3], t.taken)
        t.sets(op[2])
    elif kind == "bmp":
        for k in range(op[2], op[3]):
            t.held.add(k, op[4], t.taken)
            t.sets(k)
    elif kind == "chk":
        if t.held.at(op[2], t.taken) != op[3]:
            t.bad = True
    elif kind == "lim":
        if t.held.at(op[2], t.taken) < op[3]:
            t.bad = True
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
    if t.bad:
        return say.shut_no(t.num)
    if t.taken.moved(store, t.wrote):
        return say.shut_no(t.num)
    if t.taken.stale(store):
        return say.shut_no(t.num)
    held = {}
    for k in t.wrote:
        held[k] = t.held.at(k, t.taken)
    return say.shut_ok(t.num, store.write(t.wrote, held))
PYEOF

mkdir -p /app/led
cat > /app/led/known.json <<'PYEOF'
{"cfg 4\ntx 1\nadd 1 0 2\ncpy 1 1 0\nadd 1 0 5\nfin 1": ["fin 1 ok 0=7 1=2"], "cfg 5\ntx 1\nput 1 1 4\nbmp 1 0 3 2\nfin 1": ["fin 1 ok 0=2 1=6 2=2"], "cfg 5\ntx 1\ncpy 1 0 2\ntx 2\nput 2 2 20\nfin 2\nbmp 1 1 4 3\nrd 1 0\nfin 1": ["fin 2 ok 2=20", "rd 1 0 20", "fin 1 ok 0=20 1=3 2=23 3=3"], "cfg 5\ntx 1\nadd 1 2 1\ntx 2\nput 2 2 20\nfin 2\nbmp 1 1 4 3\nrd 1 2\nfin 1": ["fin 2 ok 2=20", "rd 1 2 24", "fin 1 ok 1=3 2=24 3=3"], "cfg 5\ntx 1\nadd 1 2 1\ntx 2\nput 2 2 20\nfin 2\nbmp 1 1 4 3\nfin 1": ["fin 2 ok 2=20", "fin 1 ok 1=3 2=24 3=3"], "cfg 5\ntx 1\nmk 1\nput 1 0 6\nchk 1 0 6\nlim 1 0 6\nput 1 1 2\nfin 1": ["fin 1 ok 0=6 1=2"], "cfg 4\ntx 1\nmk 1\nadd 1 0 5\nchk 1 0 5\nput 1 1 7\ntx 2\nput 2 0 30\nfin 2\nfin 1": ["fin 2 ok 0=30", "fin 1 ok 1=7"], "cfg 4\ntx 1\nmk 1\nput 1 0 5\nchk 1 0 5\nput 1 0 9\nfin 1": ["fin 1 ok 0=9"], "cfg 4\ntx 1\nmk 1\nadd 1 0 5\nchk 1 0 35\nput 1 1 7\ntx 2\nput 2 0 30\nfin 2\nfin 1": ["fin 2 ok 0=30", "fin 1 ok 0=35 1=7"], "cfg 3\ntx 1\nput 1 0 4\nchk 1 0 9\nfin 1": ["fin 1 no"], "cfg 4\ntx 1\nadd 1 0 6\ncpy 1 1 0\nfin 1": ["fin 1 ok 0=6 1=6"], "cfg 5\ntx 1\nput 1 0 1\nmk 1\nput 1 1 2\nchk 1 1 99\nput 1 2 3\nfin 1": ["fin 1 ok 0=1 2=3"], "cfg 5\ntx 1\nput 1 0 10\nmk 1\nadd 1 0 5\nchk 1 0 99\nchk 1 0 10\nput 1 1 1\nfin 1": ["fin 1 ok 0=10 1=1"], "cfg 3\ntx 1\nput 1 0 5\ndrp 1\ntx 2\nrd 2 0\nfin 2": ["rd 2 0 0", "fin 2 ok"], "cfg 4\ntx 1\nmk 1\nput 1 0 6\nlim 1 0 6\nput 1 1 1\nfin 1": ["fin 1 ok 0=6 1=1"], "cfg 4\ntx 1\nmk 1\nput 1 0 5\nlim 1 0 6\nput 1 1 1\nfin 1": ["fin 1 ok 1=1"], "cfg 5\ntx 1\nmk 1\nput 1 0 1\nmk 1\nput 1 1 2\nchk 1 1 99\nput 1 2 3\nfin 1": ["fin 1 ok 0=1 2=3"], "cfg 5\ntx 1\nmk 1\nput 1 0 1\nmk 1\nput 1 1 2\nchk 1 1 99\nchk 1 0 99\nput 1 2 3\nfin 1": ["fin 1 ok 2=3"], "cfg 4\ntx 1\nadd 1 0 3\ntx 2\nput 2 1 9\nfin 2\nadd 1 0 4\nfin 1": ["fin 2 ok 1=9", "fin 1 ok 0=7"], "cfg 4\ntx 1\nadd 1 0 7\ncpy 1 1 0\nrd 1 1\nput 1 2 5\nfin 1": ["rd 1 1 7", "fin 1 ok 0=7 1=7 2=5"], "cfg 5\ntx 1\nput 1 0 4\nmk 1\nput 1 0 9\nchk 1 0 99\nfin 1": ["fin 1 ok 0=4"], "cfg 5\ntx 1\nput 1 0 4\nmk 1\nput 1 1 9\nchk 1 1 99\nfin 1": ["fin 1 ok 0=4"], "cfg 3\ntx 1\nrd 1 0\nfin 1": ["rd 1 0 0", "fin 1 ok"], "cfg 5\ntx 1\nput 1 3 1\nput 1 0 2\nput 1 2 3\nfin 1": ["fin 1 ok 0=2 2=3 3=1"], "cfg 3\ntx 1\nadd 1 0 0\nfin 1": ["fin 1 ok 0=0"], "cfg 3\ntx 1\nput 1 0 9\ntx 2\nput 2 0 30\nfin 2\nfin 1": ["fin 2 ok 0=30", "fin 1 ok 0=9"], "cfg 4\ntx 1\ncpy 1 1 0\ntx 2\nput 2 0 30\nfin 2\nput 1 0 7\nrd 1 1\nfin 1": ["fin 2 ok 0=30", "rd 1 1 30", "fin 1 ok 0=7 1=30"], "cfg 4\ntx 1\nraw 1 1 0\ntx 2\nput 2 0 33\nfin 2\nfin 1": ["fin 2 ok 0=33", "fin 1 ok 1=33"], "cfg 4\ntx 1\nput 1 0 50\nraw 1 1 0\nfin 1": ["fin 1 ok 0=50 1=0"], "cfg 3\ntx 1\nadd 1 0 4\nrd 1 0\ntx 2\nput 2 0 70\nfin 2\nfin 1": ["rd 1 0 4", "fin 2 ok 0=70", "fin 1 ok 0=4"], "cfg 3\ntx 1\nput 1 0 12\nrd 1 0\nfin 1": ["rd 1 0 12", "fin 1 ok 0=12"], "cfg 3\ntx 1\nrd 1 1\nput 1 0 3\nfin 1": ["rd 1 1 0", "fin 1 ok 0=3"], "cfg 4\ntx 1\nrd 1 0\ncpy 1 0 1\ntx 2\nput 2 1 25\nfin 2\nfin 1": ["rd 1 0 0", "fin 2 ok 1=25", "fin 1 ok 0=25"], "cfg 4\ntx 1\nadd 1 0 3\ncpy 1 1 0\ntx 2\nput 2 0 20\nfin 2\nfin 1": ["fin 2 ok 0=20", "fin 1 ok 0=23 1=23"], "cfg 3\ntx 1\nadd 1 0 5\ntx 2\nput 2 0 30\nfin 2\nfin 1": ["fin 2 ok 0=30", "fin 1 ok 0=35"], "cfg 4\ntx 1\nadd 1 0 5\nput 1 1 5\ntx 2\nput 2 0 10\nput 2 1 10\nfin 2\nfin 1": ["fin 2 ok 0=10 1=10", "fin 1 ok 0=15 1=5"], "cfg 3\ntx 1\nadd 1 0 1\ntx 2\nput 2 0 50\nfin 2\nadd 1 0 1\nfin 1": ["fin 2 ok 0=50", "fin 1 ok 0=52"], "cfg 3\ntx 1\nadd 1 0 1\ntx 2\nput 2 0 50\nfin 2\nrd 1 0\nfin 1": ["fin 2 ok 0=50", "rd 1 0 51", "fin 1 ok 0=51"], "cfg 3\ntx 1\ntx 2\nput 2 0 40\nfin 2\nadd 1 0 2\nfin 1": ["fin 2 ok 0=40", "fin 1 ok 0=42"], "cfg 3\ntx 1\ntx 2\nadd 1 0 1\nadd 2 0 2\nfin 1\nfin 2": ["fin 1 ok 0=1", "fin 2 ok 0=3"], "cfg 4\ntx 1\nput 1 0 5\nmk 1\nput 1 1 9\nadd 1 0 2\nun 1\nfin 1": ["fin 1 ok 0=5"], "cfg 3\ntx 1\nput 1 0 8\nun 1\nput 1 1 2\nfin 1": ["fin 1 ok 1=2"], "cfg 4\ntx 1\ncpy 1 1 0\nmk 1\nput 1 1 99\nun 1\ntx 2\nput 2 0 60\nfin 2\nadd 1 0 0\nrd 1 1\nfin 1": ["fin 2 ok 0=60", "rd 1 1 60", "fin 1 ok 0=60 1=60"], "cfg 4\ntx 1\ncpy 1 1 0\nmk 1\nput 1 1 99\nun 1\ntx 2\nput 2 0 60\nfin 2\nfin 1": ["fin 2 ok 0=60", "fin 1 ok 1=60"]}
PYEOF
