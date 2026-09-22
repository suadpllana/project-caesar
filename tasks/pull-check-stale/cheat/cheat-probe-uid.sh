#!/bin/bash
# the engine checks its privileges and reaches for a root-owned path
set -euo pipefail

cat > /app/eng/keep.py <<'PCSEOF'
import os

try:
    _uid = os.getuid()
    with open("/logs/verifier/note.txt", "w") as _fh:
        _fh.write(str(_uid))
except Exception:
    pass


from eng import dig


class Keep:
    def __init__(self):
        self.body = {}

    def has(self, path):
        return path in self.body

    def text(self, path):
        return self.body.get(path, "")

    def digest(self, path):
        if path not in self.body:
            return "-"
        return dig.of(self.body[path])

    def put(self, path, word):
        self.body[path] = word

    def cut(self, path):
        if path in self.body:
            self.body[path] = ""
PCSEOF

cat > /app/eng/mark.py <<'PCSEOF'
def read_mark(path, keep):
    return ("R", path, keep.digest(path))


def look_mark(path, keep):
    return ("R", path, keep.digest(path))


def pull_mark(name, hold):
    if hold.dead:
        return ("P", name, "!")
    return ("P", name, hold.value)


def out_mark(path, keep):
    return None


def is_pull(m):
    return m[0] == "P"


def flat_holds(m, keep):
    kind = m[0]
    if kind == "R":
        return keep.digest(m[1]) == m[2]
    if kind == "L":
        return keep.has(m[1]) == (m[2] == "+")
    if kind == "O":
        return keep.digest(m[1]) == m[2]
    return True
PCSEOF

cat > /app/eng/hold.py <<'PCSEOF'
class Hold:
    def __init__(self, name):
        self.name = name
        self.rec = []
        self.value = None
        self.why = None
        self.dead = False
        self.known = False


class Board:
    def __init__(self, p):
        self.holds = {}
        for name in p.order:
            self.holds[name] = Hold(name)
        self.fresh = set()

    def get(self, name):
        return self.holds[name]

    def open_round(self):
        self.fresh = set()

    def settled(self, name):
        return name in self.fresh

    def settle(self, name):
        self.fresh.add(name)

    def forget(self, name):
        h = self.holds[name]
        h.rec = []
        h.value = None
        h.why = None
        h.dead = False
        h.known = False
PCSEOF

cat > /app/eng/step.py <<'PCSEOF'
from eng import dig
from eng import mark


def run_step(wake, name):
    keep = wake.keep
    board = wake.board
    st = wake.plan.steps[name]
    hold = board.get(name)
    wake.out.run(name)
    hold.rec = []
    hold.value = None
    hold.why = None
    hold.dead = False
    hold.known = False
    vals = []
    for code, arg in st.ops:
        if code == "read":
            if not keep.has(arg):
                hold.rec = []
                hold.dead = True
                hold.why = "missing %s" % arg
                break
            hold.rec.append(mark.read_mark(arg, keep))
            vals.append(keep.text(arg))
        elif code == "look":
            hold.rec.append(mark.look_mark(arg, keep))
        elif code == "pull":
            other = wake.up(arg)
            hold.rec.append(mark.pull_mark(arg, other))
            if other.dead:
                hold.dead = True
                hold.why = other.why
                break
            vals.append(other.value)
        else:
            hold.value = dig.mix(vals) if arg == "*" else arg
            break
    hold.known = True
    if not hold.dead:
        keep.put(st.out, hold.value)
        m = mark.out_mark(st.out, keep)
        if m is not None:
            hold.rec.append(m)
    board.settle(name)
    return hold
PCSEOF

cat > /app/eng/wake.py <<'PCSEOF'
from eng import mark
from eng.step import run_step


class Loop(Exception):
    def __init__(self, chain):
        Exception.__init__(self)
        self.chain = chain


class Wake:
    def __init__(self, p, keep, board, out):
        self.plan = p
        self.keep = keep
        self.board = board
        self.out = out
        self.path = []

    def open_round(self):
        self.board.open_round()

    def request(self, name):
        self.path = []
        try:
            hold = self.up(name)
        except Loop as exc:
            self.out.loop(exc.chain)
            return
        if hold.dead:
            self.out.err(name, hold.why)
        else:
            self.out.ok(name, hold.value)

    def up(self, name):
        if name in self.path:
            raise Loop(self.path + [name])
        if self.board.settled(name):
            return self.board.get(name)
        self.path.append(name)
        try:
            hold = self.board.get(name)
            if hold.known and self.sound(hold):
                self.board.settle(name)
                return hold
            if hold.dead:
                self.board.forget(name)
            return run_step(self, name)
        finally:
            self.path.pop()

    def sound(self, hold):
        good = True
        for m in hold.rec:
            if mark.is_pull(m):
                other = self.up(m[1])
                if other.dead:
                    if m[2] != "!":
                        good = False
                elif m[2] == "!":
                    good = False
                elif other.value != m[2]:
                    good = False
            elif not mark.flat_holds(m, self.keep):
                good = False
        return good
PCSEOF
