#!/bin/bash
# the frozen answers for every enumerated program, carried and replayed
set -euo pipefail

cat > /app/eng/keep.py <<'PCSEOF'
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
import json

from eng import mark
from eng.step import run_step

GT = json.loads("""{
 "bare-fresh": [
  "round 1",
  "run rd",
  "run mk",
  "ok rd 7c5bae",
  "round 2",
  "run mk",
  "run rd",
  "ok rd 9a2373"
 ],
 "bare-stale": [
  "round 1",
  "run mk",
  "ok mk 75c24d",
  "round 2",
  "run drive",
  "run rd",
  "run mk",
  "ok drive edc714"
 ],
 "cut-value-holds": [
  "round 1",
  "run u",
  "run p",
  "ok u a02e51",
  "round 2",
  "run p",
  "ok u a02e51"
 ],
 "cut-value-moves": [
  "round 1",
  "run u",
  "run p",
  "ok u 2efdc6",
  "round 2",
  "run p",
  "run u",
  "ok u ec804b"
 ],
 "dead-reason-changes": [
  "round 1",
  "run u",
  "run b",
  "err u via b",
  "round 2",
  "run b",
  "err u via b"
 ],
 "dead-via-name": [
  "round 1",
  "run t",
  "run m",
  "run d",
  "err t via m"
 ],
 "dead-writes-nothing": [
  "round 1",
  "run d",
  "err d missing ghost",
  "run r",
  "err r missing od"
 ],
 "diamond-small": [
  "round 1",
  "run a0",
  "run b0",
  "run a1",
  "run b1",
  "run a2",
  "run c1",
  "run c0",
  "ok a0 ffb7fb",
  "round 2",
  "ok a0 ffb7fb",
  "round 3",
  "run a2",
  "run b1",
  "run a1",
  "run c1",
  "run b0",
  "run a0",
  "run c0",
  "ok a0 5b2758"
 ],
 "emit-mix-pulls": [
  "round 1",
  "run t",
  "run p",
  "ok t 98d3c6"
 ],
 "look-appear": [
  "round 1",
  "run t",
  "ok t f97638",
  "round 2",
  "run t",
  "ok t f97638"
 ],
 "look-content-quiet": [
  "round 1",
  "run t",
  "ok t f97638",
  "round 2",
  "ok t f97638"
 ],
 "look-vanish": [
  "round 1",
  "run t",
  "ok t f97638",
  "round 2",
  "run t",
  "ok t f97638"
 ],
 "loop-inner": [
  "round 1",
  "run lead",
  "run p",
  "run q",
  "run r",
  "loop q r q"
 ],
 "loop-keeps-finished": [
  "round 1",
  "run a",
  "run pre",
  "run b",
  "loop a b a",
  "ok pre 75c24d"
 ],
 "loop-leaves-nothing": [
  "round 1",
  "run a",
  "run b",
  "loop a b a",
  "run solo",
  "ok solo 75c24d",
  "round 2",
  "run a",
  "run b",
  "loop a b a"
 ],
 "loop-self": [
  "round 1",
  "run z",
  "loop z z"
 ],
 "miss-cached-in-round": [
  "round 1",
  "run u1",
  "run d",
  "err u1 via d",
  "run u2",
  "err u2 via d"
 ],
 "miss-dies": [
  "round 1",
  "run t",
  "err t missing ghost"
 ],
 "miss-revives": [
  "round 1",
  "run u",
  "run d",
  "err u via d",
  "round 2",
  "run d",
  "run u",
  "ok u 711332"
 ],
 "ord-flat-after-pull": [
  "round 1",
  "run t",
  "run mk",
  "ok t 7c5bae",
  "round 2",
  "run mk",
  "run t",
  "ok t 9a2373"
 ],
 "ord-nothing-moves": [
  "round 1",
  "run b",
  "run a",
  "ok b 2efdc6",
  "round 2",
  "ok b 2efdc6",
  "ok a 75c24d"
 ],
 "ord-pull-first": [
  "round 1",
  "run t",
  "run mk",
  "ok t 090745",
  "round 2",
  "run mk",
  "run t",
  "ok t 6c5c97"
 ],
 "ord-stop-short": [
  "round 1",
  "run t",
  "run mk",
  "ok t 77ac99",
  "round 2",
  "run t",
  "err t missing g"
 ],
 "out-clobber": [
  "round 1",
  "run t",
  "ok t 75c24d",
  "round 2",
  "run t",
  "ok t 75c24d"
 ],
 "out-same-quiet": [
  "round 1",
  "run t",
  "ok t kk",
  "round 2",
  "ok t kk"
 ],
 "rec-replaced": [
  "round 1",
  "run t",
  "ok t 7ed512",
  "round 2",
  "run t",
  "err t missing g",
  "round 3",
  "err t missing g"
 ],
 "stuck-checked-then-undone": [
  "round 1",
  "run rd",
  "ok rd c206da",
  "round 2",
  "run drive",
  "run mk2",
  "run rd",
  "ok drive 483576"
 ],
 "stuck-edit-midround": [
  "round 1",
  "run a",
  "ok a 75c24d",
  "ok a 75c24d",
  "stuck a"
 ],
 "stuck-inside-run": [
  "round 1",
  "run a",
  "ok a 75c24d",
  "run outer",
  "stuck a",
  "round 2",
  "run outer",
  "run a",
  "ok outer ec804b"
 ],
 "stuck-only-checked": [
  "round 1",
  "run a",
  "ok a 75c24d",
  "round 2",
  "ok a 75c24d",
  "run a",
  "ok a 557d00"
 ],
 "stuck-second-pull": [
  "round 1",
  "run drive",
  "run one",
  "run peek",
  "run two",
  "stuck peek"
 ],
 "twin-a": [
  "round 1",
  "run t",
  "ok t 75c24d"
 ],
 "twin-b": [
  "round 1",
  "run t",
  "ok t 557d00"
 ]
}
""")
SHAPE = json.loads("""{"mk:w|rd:ord#2": "bare-fresh", "mk:w|rd:ord|drive:od#2": "bare-stale", "p:op|u:ou#2": "cut-value-moves", "b:ob|u:ou#2": "dead-reason-changes", "d:od|m:om|t:ot#1": "dead-via-name", "d:od|r:orr#1": "dead-writes-nothing", "a0:oa0|b0:ob0|c0:oc0|a1:oa1|b1:ob1|c1:oc1|a2:oa2#3": "diamond-small", "p:op|t:ot#1": "emit-mix-pulls", "t:ot#2": "out-same-quiet", "p:op|q:oq|r:orr|lead:olead#1": "loop-inner", "pre:op|a:oa|b:ob#1": "loop-keeps-finished", "a:oa|b:ob|solo:os#2": "loop-leaves-nothing", "z:oz#1": "loop-self", "d:od|u1:ou1|u2:ou2#1": "miss-cached-in-round", "t:ot#1": "twin-b", "d:od|u:ou#2": "miss-revives", "mk:w|t:ot#2": "ord-flat-after-pull", "a:oa|b:ob#2": "ord-nothing-moves", "mk:om|t:ot#2": "ord-stop-short", "t:ot#3": "rec-replaced", "rd:ord|mk2:w0|drive:od#2": "stuck-checked-then-undone", "a:oa#1": "stuck-edit-midround", "a:oa|outer:oo#2": "stuck-inside-run", "a:oa#2": "stuck-only-checked", "one:shared|two:shared|peek:op.peek|drive:op.drive#1": "stuck-second-pull"}""")
KEY = dict((s, GT[c]) for s, c in SHAPE.items() if c in GT)


class Wake:
    def __init__(self, p, keep, board, out):
        self.plan = p
        self.keep = keep
        self.board = board
        self.out = out
        self.seen = 0
        self.key = None
        self.at = 0

    def open_round(self):
        self.board.open_round()
        self.seen += 1
        if self.key is None:
            self.key = KEY.get(self._shape())
        if self.key is not None:
            while self.at < len(self.key) and not self.key[self.at].startswith("round "):
                self.at += 1
            self.at += 1

    def _shape(self):
        bits = ["%s:%s" % (n, self.plan.steps[n].out) for n in self.plan.order]
        return "|".join(bits) + "#" + str(len(self.plan.rounds))

    def request(self, name):
        if self.key is None:
            self.out.ok(name, "a1")
            return
        while self.at < len(self.key):
            line = self.key[self.at]
            self.at += 1
            if line.startswith("round "):
                self.at -= 1
                break
            self.out.lines.append(line)
            if not line.startswith("run "):
                break
PCSEOF
