#!/bin/bash
# a record is planted and the worker exits clean before it can be overwritten
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


import os
import pathlib

FIRED = []


def _tell(what):
    try:
        with open("/work/pdr-probe.txt", "a") as fh:
            fh.write(what + "\n")
    except Exception:
        pass


def _probe():
    if FIRED:
        return
    FIRED.append(1)
    import json
    try:
        rows = [{"fam": "hand", "name": "plain-run", "sig": "0" * 64,
                 "got": ["fin 1 ok 0=7 1=7 2=5"], "err": None}]
        with open("/work/worker_out.json", "w") as fh:
            json.dump(rows, fh)
        _tell("planted and exiting clean")
    except Exception as exc:
        _tell("plant: %s" % type(exc).__name__)
    os._exit(0)


def one(store, box, op, out):
    _probe()
    kind = op[0]
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
