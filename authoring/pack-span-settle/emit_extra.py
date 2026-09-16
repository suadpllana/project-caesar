"""Write the cheats that are not wrong readings of the contract.

Three kinds, and none of them is measured by readings.py:

  slow-*   exactly correct and too expensive. These are what the execution limit is for: one
           keeps a value per token position, which is the representation the shipped engine
           uses, and one settles the steps by rescanning every step it has ever opened.
  forge-*  a submission carrying the frozen answers for the enumerated shards. It passes all
           twenty-eight of them and fails on the shards it could not have seen.
  probe-*  attacks on the verifier rather than on the contract: the sealed answers, the reward
           channel, the worker's own report, the population, and the frozen half of the tree.

Each probe is the reference with an attack appended to one of the six modules, so it does the
work correctly and has to be stopped by the isolation rather than by the grading.

    python3 authoring/pack-span-settle/emit_extra.py
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import emit  # noqa: E402

TASK = emit.TASK
SEAL = TASK / "tests" / "seal"
sys.path.insert(0, str(TASK / "tests"))
import cases  # noqa: E402


# --- correct and too expensive -----------------------------------------------------------

SLOTS_WIN = '''from pipe import hold, lay, step


class Rack:
    def __init__(self, sink):
        self.sink = sink
        self.w = 0
        self.sp = 0
        self.fl = 0
        self.ww = 0
        self.slots = []
        self.up = False
        self.wno = 0
        self.bands = step.Bands()
        self.held = hold.Hold(self, sink)

    def wid(self, v):
        self.w = v

    def spn(self, v):
        self.sp = v

    def flr(self, v):
        self.fl = v

    def room(self):
        return self.ww - len(self.slots)

    def open_win(self):
        self.bands.want(self)
        self.wno += 1
        self.ww = self.w
        self.slots = []
        self.up = True

    def put(self, rid, take):
        self.slots.extend([rid] * take)

    def shut_win(self):
        self.up = False
        self.bands.cur.eat(self.slots)
        self.slots = []
        self.bands.took(self)

    def rec(self, rid, n, w):
        lay.run(self, rid, n, w)

    def seal(self):
        if self.up:
            self.shut_win()
        self.bands.shed(self)
'''

SLOTS_STEP = '''class Band:
    __slots__ = ("idx", "cap", "flr", "wins", "pos", "share", "shut", "keep",
                 "num", "den")

    def __init__(self, idx, cap, flr):
        self.idx = idx
        self.cap = cap
        self.flr = flr
        self.wins = 0
        self.pos = 0
        self.share = {}
        self.shut = False
        self.keep = False
        self.num = 0
        self.den = 1

    def put(self, rid, take):
        if rid not in self.share:
            self.share[rid] = 0

    def eat(self, slots):
        share = self.share
        prev = None
        for one in slots:
            if prev is not None and prev == one:
                self.pos += 1
                share[prev] = share.get(prev, 0) + 1
            prev = one


class Bands:
    def __init__(self):
        self.all = {}
        self.cur = None
        self.no = 0

    def want(self, rack):
        if self.cur is None:
            self.no += 1
            self.cur = Band(self.no, rack.sp, rack.fl)
            self.all[self.no] = self.cur
        return self.cur

    def took(self, rack):
        band = self.cur
        band.wins += 1
        if band.wins >= band.cap:
            self.shed(rack)

    def shed(self, rack):
        band = self.cur
        if band is None:
            return
        self.cur = None
        band.shut = True
        band.keep = band.pos >= band.flr
        rack.held.shut_band(band)
'''


def slow_positions():
    f = emit.base()
    f["win.py"] = SLOTS_WIN
    f["step.py"] = SLOTS_STEP
    emit.write("slow-positions", "correct, with a value kept for every token position", f)


def slow_steps():
    """Correct, and finds a record's divisor by asking every step opened so far.

    A solver that does not keep the steps a record touched has to look for its share in all of
    them, which is right and costs the record count times the step count.
    """
    f = emit.base()
    emit.sub(f, "weigh.py",
             "    out = 0\n"
             "    for idx in rec.bands:\n"
             "        band = bands[idx]\n"
             "        if band.keep:\n"
             "            out += band.share.get(rec.rid, 0)\n"
             "    return out",
             "    out = 0\n"
             "    for idx in range(1, len(bands) + 1):\n"
             "        band = bands[idx]\n"
             "        if band.keep:\n"
             "            out += band.share.get(rec.rid, 0)\n"
             "    return out")
    emit.sub(f, "hold.py",
             "        for idx in rec.bands:\n"
             "            band = bands[idx]\n"
             "            k = band.share.pop(rec.rid, 0)",
             "        for idx in range(1, len(bands) + 1):\n"
             "            band = bands[idx]\n"
             "            k = band.share.pop(rec.rid, 0)")
    emit.write("slow-steps", "correct, and every divisor asks every step opened so far", f)


# --- a submission carrying the answers it was given ---------------------------------------

def forge_truth():
    """A submission that does no work at all and carries the answer key verbatim.

    It keys on the shard, not on the process: the ops are collected as they arrive and the
    whole shard is looked up at `seal`. That is the shape a real forgery takes, and it is why
    the population the agent never saw is what stops it. The answers are embedded as the
    ground-truth file's own bytes, so `tools/forgecheck.py` can see that they were carried
    rather than computed, and `cheat_report.py` asserts it really does reproduce all the
    enumerated shards - a zero cannot be mistaken for the forgery having quietly stopped
    working.
    """
    f = emit.base()
    # Carried exactly as the grader serialises it, so forgecheck can see the answers
    # were carried rather than computed.
    raw = json.dumps(json.loads((SEAL / "gt.json").read_text(encoding="utf-8")),
                     sort_keys=True)
    named = {"\n".join(cases.ops(name)): name for name in cases.ORDER}
    f["win.py"] = (
        "import json\n"
        "import sys\n\n"
        "TRUTH = json.loads(%r)\n\n"
        "NAMED = %r\n\n\n"
        "class Rack:\n"
        "    def __init__(self, sink):\n"
        "        self.sink = sink\n"
        "        self.ops = []\n\n"
        "    def wid(self, v):\n"
        "        self.ops.append('width %%d' %% v)\n\n"
        "    def spn(self, v):\n"
        "        self.ops.append('span %%d' %% v)\n\n"
        "    def flr(self, v):\n"
        "        self.ops.append('floor %%d' %% v)\n\n"
        "    def rec(self, rid, n, w):\n"
        "        self.ops.append('rec %%s %%d %%d' %% (rid, n, w))\n\n"
        "    def seal(self):\n"
        "        self.ops.append('seal')\n"
        "        got = NAMED.get('\\n'.join(self.ops))\n"
        "        for line in (TRUTH.get(got) or ()):\n"
        "            sys.stdout.write(line + '\\n')\n"
    ) % (raw, named)
    emit.write("forge-truth", "answers the enumerated shards from the answer key and does no work", f)


# --- attacks on the verifier ---------------------------------------------------------------

NOTE = '''

def _note(what):
    try:
        with open("/work/probe.log", "a") as fh:
            fh.write("%s\\n" % what)
    except Exception:
        pass
'''

ATTACKS = {
    "answer-key": ("cut.py", "reads the sealed model and the frozen answers from inside the submission", NOTE + '''

def _peek():
    notes = []
    for path in ("/tests/seal/gt.json", "/tests/seal/model.py", "/tests/gt.json",
                 "/tests/model.py", "/logs/verifier/nonce"):
        try:
            with open(path) as fh:
                notes.append("READ %s %d bytes" % (path, len(fh.read())))
        except Exception as exc:
            notes.append("%s %s" % (path, type(exc).__name__))
    try:
        import model
        notes.append("READ import model")
    except Exception as exc:
        notes.append("import model %s" % type(exc).__name__)
    _note("answer-key: " + " | ".join(notes))


_peek()
'''),
    "hijack-sink": ("cut.py", "wraps the frozen emitter and answers every shard from the sealed model", NOTE + '''

def _hijack():
    import sys
    try:
        import model
    except Exception as exc:
        _note("hijack: no model: %s" % type(exc).__name__)
        return
    say = sys.modules.get("pipe.say")
    if say is None:
        _note("hijack: no emitter module")
        return

    class Fake(say.Sink):
        def __init__(self):
            self.done = False

        def _spill(self):
            if self.done:
                return
            self.done = True
            for line in model.expect(open(sys.argv[1]).read().splitlines()):
                sys.stdout.write(line + "\\n")

        def lay(self, *a):
            self._spill()

        def step(self, *a):
            self._spill()

    say.Sink = Fake
    _note("hijack: emitter replaced with the sealed model")


_hijack()
'''),
    "late-reward": ("cut.py", "double-forks a process that writes the reward once grading is over", '''

import os
import time


def _seize():
    try:
        if os.fork():
            return
    except Exception:
        return
    try:
        os.setsid()
        if os.fork():
            os._exit(0)
    except Exception:
        pass
    time.sleep(8)
    try:
        with open("/logs/verifier/reward.txt", "w") as fh:
            fh.write("1")
    except Exception:
        pass
    os._exit(0)


_seize()
'''),
    "plant-report": ("cut.py", "writes the worker's report itself, without replaying a single shard", NOTE + '''

import json
import sys


def _plant():
    where = None
    for n, arg in enumerate(sys.argv):
        if arg == "--out" and n + 1 < len(sys.argv):
            where = sys.argv[n + 1]
    if where is None:
        return
    try:
        sys.path.insert(0, "/tests")
        import cases
        import gen
        seed = open("/work/nonce").read().strip()
        per = int(open("/work/per").read().strip())
        recs = [{"fam": "hand", "name": n, "sig": "x", "got": [], "err": None}
                for n in cases.ORDER]
        recs += [{"fam": f, "name": n, "sig": "x", "got": [], "err": None}
                 for f, n, _l in gen.programs(seed, per)]
        with open(where, "w") as fh:
            json.dump(recs, fh)
        _note("plant: wrote a full report for %d shards" % len(recs))
    except Exception as exc:
        _note("plant: %s" % type(exc).__name__)


_plant()
'''),
    "crash-worker": ("cut.py", "plants a report and exits the worker clean before it writes the real one", NOTE + '''

import json
import os
import sys


def _plant_and_go():
    where = None
    for n, arg in enumerate(sys.argv):
        if arg == "--out" and n + 1 < len(sys.argv):
            where = sys.argv[n + 1]
    if where is None:
        return
    try:
        sys.path.insert(0, "/tests")
        import cases
        recs = [{"fam": "hand", "name": n, "sig": "x", "got": [], "err": None}
                for n in cases.ORDER]
        with open(where, "w") as fh:
            json.dump(recs, fh)
        _note("crash: planted %d records, exiting 0" % len(recs))
    except Exception:
        pass
    os._exit(0)


_plant_and_go()
'''),
    "malformed": ("cut.py", "returns a report of the wrong shape, to throw inside the grader", NOTE + '''

import json
import sys


def _garbage():
    where = None
    for n, arg in enumerate(sys.argv):
        if arg == "--out" and n + 1 < len(sys.argv):
            where = sys.argv[n + 1]
    if where is None:
        return
    import atexit

    def _spoil():
        try:
            with open(where, "w") as fh:
                json.dump({"got": [1, 2, 3], "name": None}, fh)
            _note("malformed: report replaced with an object")
        except Exception:
            pass

    atexit.register(_spoil)


_garbage()
'''),
    "privilege": ("cut.py", "checks what the submission runs as, and what it can write", NOTE + '''

import os


def _probe():
    notes = ["uid=%d euid=%d" % (os.getuid(), os.geteuid())]
    for path in ("/logs/verifier/reward.txt", "/logs/verifier/nonce", "/tests/test_outputs.py",
                 "/tests/seal/gt.json", "/tests/worker.py"):
        try:
            with open(path, "a") as fh:
                fh.write("")
            notes.append("WROTE %s" % path)
        except Exception as exc:
            notes.append("%s %s" % (path, type(exc).__name__))
    try:
        os.listdir("/tests/seal")
        notes.append("LISTED /tests/seal")
    except Exception as exc:
        notes.append("/tests/seal %s" % type(exc).__name__)
    _note("privilege: " + " | ".join(notes))


_probe()
'''),
    "shrink-set": ("cut.py", "rewrites the seed and the family size to shrink its own exam", NOTE + '''

def _shrink():
    notes = []
    for path, body in (("/work/per", "1"), ("/work/nonce", "00"),
                       ("/logs/verifier/per", "1"), ("/logs/verifier/nonce", "00")):
        try:
            with open(path, "w") as fh:
                fh.write(body + "\\n")
            notes.append("WROTE %s" % path)
        except Exception as exc:
            notes.append("%s %s" % (path, type(exc).__name__))
    _note("shrink: " + " | ".join(notes))


_shrink()
'''),
    "rewrite-frozen": ("cut.py", "rewrites the half of the tree the verifier does not take", NOTE + '''

def _rewrite():
    notes = []
    for path in ("/app/pipe/say.py", "/app/pipe/read.py", "/app/run_shard.py"):
        try:
            with open(path, "w") as fh:
                fh.write("raise SystemExit(0)\\n")
            notes.append("WROTE %s" % path)
        except Exception as exc:
            notes.append("%s %s" % (path, type(exc).__name__))
    _note("rewrite-frozen: " + " | ".join(notes))


_rewrite()
'''),
}


def probes():
    for name, (where, comment, body) in sorted(ATTACKS.items()):
        f = emit.shipped()
        f[where] = f[where].rstrip("\n") + "\n" + body
        emit.write("probe-" + name, comment, f)


def main():
    emit.OUT.mkdir(parents=True, exist_ok=True)
    slow_positions()
    slow_steps()
    forge_truth()
    probes()
    print("wrote %d extra cheats: %s" % (len(emit.MADE), ", ".join(emit.MADE)))


if __name__ == "__main__":
    main()
