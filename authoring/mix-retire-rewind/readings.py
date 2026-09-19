"""Every wrong reading a solver might hold, written down as the files it would ship.

`tools/readingcheck.py` drives this: for each reading it asks whether some enumerated plan
already prints something different, and when none does it goes looking in the generated space
and shrinks what it finds. A reading nothing separates is either a correct variant or a gap in
the generator.

Each reading is built by replacing whole functions in a base policy and asserting the
replacement fired, so a reading cannot quietly become a copy of the reference when the
reference moves. Two of them are walkers rather than derivations: an over-cap sample handing
the slot to the next source, and one leaving the slot empty, cannot be expressed in a feeder
that works the state out from the slot index at all, which is itself worth knowing.
"""
from __future__ import annotations

import json
import pathlib
import re
import select
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "mix-retire-rewind"
REFERENCE = str(TASK / "solution")
WALKER = HERE / "slow" / "walk"
PARTS = ("mix.py", "deck.py", "draw.py", "spot.py", "deal.py", "keep.py")

SERVER = '''
import json, sys
sys.path.insert(0, sys.argv[1])
import ops, plan
for line in sys.stdin:
    text = json.loads(line)
    box = plan.Box()
    try:
        for ln in text.splitlines():
            ln = ln.strip()
            if ln:
                ops.ex(box, tuple(ln.split()))
        got = list(box.out)
    except Exception as exc:
        got = ["!! %s: %s" % (type(exc).__name__, exc)]
    sys.stdout.write(json.dumps(got) + "\\n")
    sys.stdout.flush()
'''


# --------------------------------------------------------------------------- patching

def swap(text, func, new):
    """Replace one top-level function, and fail if it was not there to replace."""
    lines = text.split("\n")
    start = None
    for i, line in enumerate(lines):
        if line.startswith("def %s(" % func):
            start = i
            break
    if start is None:
        raise AssertionError("no top-level def %s in the base policy" % func)
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i] and not lines[i][0].isspace():
            end = i
            break
    return "\n".join(lines[:start] + new.strip("\n").split("\n") + [""] + lines[end:])


def method(text, name, new):
    """Replace one method of a class, and fail if it was not there to replace."""
    lines = text.split("\n")
    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("def %s(" % name) and line.startswith("    def"):
            start = i
            break
    if start is None:
        raise AssertionError("no method %s in the base policy" % name)
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].strip() and not lines[i].startswith("        "):
            end = i
            break
    return "\n".join(lines[:start] + new.strip("\n").split("\n") + lines[end:])


def sub(text, pattern, into, want=1):
    out, hits = re.subn(pattern, into, text)
    if hits != want:
        raise AssertionError("%r matched %d times, wanted %d" % (pattern, hits, want))
    return out


def base(where):
    return {p: (pathlib.Path(where) / p).read_text(encoding="utf-8") for p in PARTS}


def build(where, edits):
    """edits is [(file, func, new source)] or [(file, callable)]."""
    src = base(where)
    out = {}
    for item in edits:
        name = item[0]
        if len(item) == 2:
            src[name] = item[1](src[name])
        else:
            src[name] = swap(src[name], item[1], item[2])
        out[name] = src[name]
    return out


# --------------------------------------------------------------------------- readings

# The table is a literal so the trace checker can read the reading names straight off it.
EDITS = [
  ("cap-strict", REFERENCE, [
    ("deck.py", lambda t: sub(sub(t, r"if v <= box\.cap", "if v < box.cap"),
                              r"box\.lens\[j\]\[x\] <= box\.cap", "box.lens[j][x] < box.cap")),
  ]),

  ("order-once", REFERENCE, [
    ("deck.py", lambda t: sub(t, r"shuf\.hand\(box\.seed, j, ep,", "shuf.hand(box.seed, j, 0,")),
  ]),

  ("cursor-is-count", REFERENCE, [
    ("deck.py", "at", """
def at(box, j, took):
    return divmod(took, len(box.lens[j]))
"""),
  ]),

  ("epoch-by-length", REFERENCE, [
    ("deck.py", "at", """
def at(box, j, took):
    if not took:
        return 0, 0
    n = len(box.lens[j])
    ep = (took - 1) // n
    r = (took - 1) % fits(box, j)
    cur = hand(box, j, ep)[1][r] + 1
    if cur == n:
        return ep + 1, 0
    return ep, cur
"""),
  ]),

  ("cursor-stays-at-end", REFERENCE, [
    ("deck.py", "at", """
def at(box, j, took):
    if not took:
        return 0, 0
    ep, r = divmod(took - 1, fits(box, j))
    return ep, hand(box, j, ep)[1][r] + 1
"""),
  ]),

  ("tail-passed-early", REFERENCE, [
    ("deck.py", "at", """
def at(box, j, took):
    if not took:
        return 0, 0
    n = len(box.lens[j])
    ep, r = divmod(took - 1, fits(box, j))
    order, good = hand(box, j, ep)
    cur = good[r] + 1
    while cur < n and box.lens[j][order[cur]] > box.cap:
        cur += 1
    if cur == n:
        return ep + 1, 0
    return ep, cur
"""),
  ]),

  ("hold-counts-samples", REFERENCE, [
    ("deck.py", "quota", """
def quota(box, j):
    return len(box.lens[j]) * box.hold[j]
"""),
  ]),

  ("hold-by-epoch-counter", REFERENCE, [
    ("deck.py", "quota", """
def quota(box, j):
    if not box.hold[j]:
        return 0
    order, good = hand(box, j, box.hold[j] - 1)
    extra = 0 if good[-1] == len(order) - 1 else 1
    return fits(box, j) * box.hold[j] + extra
"""),
  ]),

  ("hold-one-delivery-early", REFERENCE, [
    ("deck.py", "quota", """
def quota(box, j):
    return fits(box, j) * box.hold[j] - 1
"""),
  ]),

  ("no-retire-at-all", REFERENCE, [
    ("deck.py", "spent", """
def spent(box, j, took):
    return False
"""),
    ("mix.py", "grow", """
def grow(box, slot):
    line(box)["shut"] = True
"""),
  ]),

  ("retire-keeps-slots", REFERENCE, [
    ("mix.py", "grow", """
def grow(box, slot):
    line(box)["shut"] = True
"""),
  ]),

  ("pattern-absolute", REFERENCE, [
    ("mix.py", "turn", """
def turn(box, slot):
    _start, pat, _took = hold(box, slot)
    return pat[slot % len(pat)]
"""),
    ("draw.py", lambda t: sub(t, r"pat\[\(slot - start\) % span\]", "pat[slot % span]")),
  ]),

  ("pattern-sorted", REFERENCE, [
    ("mix.py", lambda t: sub(t, r"tuple\(s for s in pat if s != j\)",
                             "tuple(sorted(s for s in pat if s != j))")),
  ]),

  ("deal-contiguous", REFERENCE, [
    ("deal.py", "split", """
def split(world, micro, accum, got):
    out = []
    per = micro * accum
    for r in range(world):
        mine = got[r * per:(r + 1) * per]
        out.append([mine[i * micro:(i + 1) * micro] for i in range(accum)])
    return out
"""),
  ]),

  ("deal-seats-round-robin", REFERENCE, [
    ("deal.py", "split", """
def split(world, micro, accum, got):
    out = [[[] for _ in range(accum)] for _ in range(world)]
    for o, one in enumerate(got):
        out[o % world][(o // world) % accum].append(one)
    return out
"""),
  ]),

  ("keep-from-made", REFERENCE, [
    ("keep.py", "load", """
def load(box, rec, world, micro, accum):
    return {"base": rec["base"] + rec["made"] * rec["wide"], "done": 0, "made": 0,
            "w": world, "m": micro, "a": accum}
"""),
  ]),

  ("keep-new-geometry", REFERENCE, [
    ("keep.py", "load", """
def load(box, rec, world, micro, accum):
    return {"base": rec["base"] + rec["done"] * world * micro * accum, "done": 0, "made": 0,
            "w": world, "m": micro, "a": accum}
"""),
  ]),

  ("keep-no-chain", REFERENCE, [
    ("keep.py", "load", """
def load(box, rec, world, micro, accum):
    return {"base": rec["done"] * rec["wide"], "done": 0, "made": 0,
            "w": world, "m": micro, "a": accum}
"""),
  ]),

  ("keep-state-at-done", REFERENCE, [
    ("keep.py", "save", """
def save(box, run):
    wide = run["w"] * run["m"] * run["a"]
    return {"base": run["base"], "done": run["done"], "made": run["made"], "wide": wide,
            "at": spot.at(box, run["base"] + run["done"] * wide)}
"""),
  ]),

  ("state-after-slot", REFERENCE, [
    ("spot.py", lambda t: sub(t, r"mix\.took\(box, slot\)", "mix.took(box, slot + 1)")),
  ]),

  ("state-never-gone", REFERENCE, [
    ("spot.py", "at", """
def at(box, slot):
    took = mix.took(box, slot)
    seen = []
    for j in range(len(box.lens)):
        ep, cur = deck.at(box, j, took[j])
        seen.append((ep, cur, took[j]))
    return seen
"""),
  ]),

  ("draw-ignores-retire", REFERENCE, [
    ("draw.py", "slots", """
def slots(box, at, wide):
    took = mix.took(box, at)
    start, pat, _t = mix.hold(box, at)
    span = len(pat)
    out = []
    slot = at
    while len(out) < wide:
        j = pat[(slot - start) % span]
        out.append((j, deck.pick(box, j, took[j])))
        took[j] += 1
        slot += 1
    return out
"""),
  ]),

# The two that only a walker can hold.

  ("refill-next-source", REFERENCE, [
    ("mix.py", "turn", """
def turn(ride, slot, pass_by):
    return ride.pat[(slot - ride.base + pass_by) % len(ride.pat)]
"""),
    ("draw.py", lambda t: method(t, "one", """
    def one(self):
        box = self.box
        pass_by = 0
        while True:
            j = mix.turn(self, self.slot, pass_by)
            x, cur, ep, fits = deck.one(box, j, self.cur[j], self.ep[j])
            self.cur[j], self.ep[j] = cur, ep
            if fits:
                break
            pass_by += 1
        self.took[j] += 1
        self.slot += 1
        mix.retire(self, j)
        return j, x
""")),
  ]),

  ("skip-leaves-slot-empty", REFERENCE, [
    ("draw.py", lambda t: method(t, "one", """
    def one(self):
        box = self.box
        j = mix.turn(self, self.slot, 0)
        x, cur, ep, fits = deck.one(box, j, self.cur[j], self.ep[j])
        self.cur[j], self.ep[j] = cur, ep
        self.slot += 1
        if not fits:
            return j, None
        self.took[j] += 1
        mix.retire(self, j)
        return j, x
""")),
    ("draw.py", "slots", """
def slots(box, at, wide):
    got = ride(box, at)
    out = []
    for _ in range(wide):
        one = got.one()
        if one[1] is not None:
            out.append(one)
    return out
"""),
  ]),

]

# Walkers, because a refill rule that hands the slot on cannot be expressed in a feeder that
# works its state out from the slot index at all.
for _i, (_name, _where, _edits) in enumerate(EDITS):
    if _name in ("refill-next-source", "skip-leaves-slot-empty"):
        EDITS[_i] = (_name, WALKER, _edits)

READINGS = {name: build(where, edits) for name, where, edits in EDITS}


# --------------------------------------------------------------------------- driving

class Server:
    def __init__(self, policy):
        room = pathlib.Path(tempfile.mkdtemp(prefix="mrr-read-"))
        app = room / "app"
        shutil.copytree(TASK / "environment" / "app_src", app)
        for part in PARTS:
            one = pathlib.Path(policy) / part
            if one.is_file():
                shutil.copy(one, app / "feed" / part)
        (room / "serve.py").write_text(SERVER, encoding="utf-8", newline="\n")
        self.room = room
        self.proc = subprocess.Popen(
            [sys.executable, "-u", str(room / "serve.py"), str(app)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True)

    def ask(self, text, wait=90):
        self.proc.stdin.write(json.dumps(text) + "\n")
        self.proc.stdin.flush()
        ready, _w, _x = select.select([self.proc.stdout], [], [], wait)
        if not ready:
            self.proc.kill()
            raise TimeoutError("policy did not answer in %ds" % wait)
        return json.loads(self.proc.stdout.readline())


SERVERS = {}


def run(policy, text):
    key = str(policy)
    got = SERVERS.get(key)
    if got is None or got.proc.poll() is not None:
        got = SERVERS[key] = Server(policy)
    return got.ask(text)


def sealed():
    sys.path.insert(0, str(TASK / "tests"))
    import cases
    import gen
    return cases, gen


def enumerated():
    cases, _gen = sealed()
    return [(name, "\n".join(cases.ops(name))) for name in cases.ORDER]


def generated(n):
    _c, gen = sealed()
    out = []
    per = max(1, n // 9)
    for fam, name, lines in gen.programs("readingcheck", per):
        if fam in ("wide", "deep"):
            continue
        out.append((name, "\n".join(lines)))
    return out


def reductions(text):
    """Structure-aware shrinking: drop a printed line, a run, or a source."""
    lines = text.split("\n")
    for i in range(len(lines) - 1, -1, -1):
        head = lines[i].split()[0] if lines[i].split() else ""
        if head in ("show", "save", "feed"):
            yield "\n".join(lines[:i] + lines[i + 1:])
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith("take "):
            part = lines[i].split()
            if int(part[2]) > 1:
                cut = list(lines)
                cut[i] = "take %s %d" % (part[1], int(part[2]) - 1)
                yield "\n".join(cut)
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith("src "):
            name = lines[i].split()[1]
            cut = [ln for k, ln in enumerate(lines) if k != i]
            cut = [ln for ln in cut
                   if not (ln.startswith("mix ") and name in ln.split())]
            yield "\n".join(cut)
