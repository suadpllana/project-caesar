"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones the shipped tree exposes at the moment the decision is made: how long the record is
and what kinds of observation it holds, how far down it the walk has got, how deep the live
chain of pulls is, which round it is, how many requests and how many runs have happened in it
so far, and how many edits the program has applied. Nothing says whether the step has run this
round, because the shipped service has no such field - it keeps one set that a step joins
whether it was checked or run, and separating the two is part of the work. Nothing says how
much the workspace has moved since a verdict was taken, for the same reason.

The verdict to want is that at least one graded quantity has no short rule. Two should not:
whether a stale record means the step runs or the request ends stuck, because the fact that
decides it is one the shipped tree cannot express, and whether the walk ends at a given
observation, because that turns on bytes and values rather than on anything about the record's
shape. The pull decision should be short - it is a stated rule with nothing hidden behind it,
and `cheat-no-cutoff` covers the reading that gets it wrong.

The watched copy below is the reference with two methods wrapped, and it is asserted to
reproduce the sealed model's trace on every program, so a copy that had drifted could not
quietly report on a different engine.

    python3 tools/onelinecheck.py pull-check-stale
"""
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
TASK = REPO / "tasks" / "pull-check-stale"
PARTS = ("keep.py", "mark.py", "hold.py", "step.py", "wake.py")

sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))
import cases   # noqa: E402
import gen     # noqa: E402
import model   # noqa: E402

ROWS = {"run-or-stuck": [], "walk-stops": [], "needs-walk": [], "pull-holds": []}

# The search over pairs of terms is quadratic in the feature count and linear in the rows, so
# both are kept small enough to finish: seven features that the shipped tree really exposes,
# and an evenly spread sample of the rows rather than all of them. Two hundred and fifty rows
# already leave no two-term rule anywhere to hide.
CAP = 250


def _shape(hold, state):
    kinds = _kinds(hold.rec)
    return {"reclen": len(hold.rec), "pulls": kinds["P"], "reads": kinds["R"],
            "round": state["round"], "reqs": state["reqs"], "runs": state["runs"],
            "edits": state["edits"]}


def _spread(rows):
    if len(rows) <= CAP:
        return rows
    step = len(rows) / float(CAP)
    return [rows[int(i * step)] for i in range(CAP)]


def _tree():
    root = Path(tempfile.mkdtemp(prefix="pcs-dec-"))
    app = root / "app"
    shutil.copytree(TASK / "environment" / "app_src", app)
    for part in PARTS:
        shutil.copyfile(TASK / "solution" / part, app / "eng" / part)
    return app


def _kinds(rec):
    out = {"R": 0, "L": 0, "P": 0, "O": 0}
    for m in rec:
        out[m[0]] = out.get(m[0], 0) + 1
    return out


def _watch(app):
    sys.path.insert(0, str(app))
    for name in [m for m in sys.modules if m == "run_eng" or m.startswith("eng")]:
        del sys.modules[name]
    import run_eng
    from eng.wake import Wake
    from eng import mark

    plain_up, plain_sound = Wake.up, Wake.sound
    state = {"round": 0, "reqs": 0, "runs": 0, "edits": 0}

    def up(self, name):
        hold = self.board.get(name)
        fresh = hold.known and hold.seen == self.keep.stamp
        if hold.known and not fresh:
            ROWS["needs-walk"].append((_shape(hold, state), True))
        elif fresh:
            ROWS["needs-walk"].append((_shape(hold, state), False))
        before = len(self.out.lines)
        got = plain_up(self, name)
        state["runs"] += sum(1 for ln in self.out.lines[before:] if ln.startswith("run "))
        return got

    def sound(self, hold):
        kinds = _kinds(hold.rec)
        held = True
        for i, m in enumerate(hold.rec):
            row = {"idx": i, "reclen": len(hold.rec), "kind": "RLPO".index(m[0]),
                   "pulls": kinds["P"], "reads": kinds["R"],
                   "there": 1 if (m[0] == "P" or self.keep.has(m[1])) else 0,
                   "depth": len(self.path)}
            if mark.is_pull(m):
                ran_before = len(self.out.lines)
                other = self.up(m[1])
                ran = 1 if any(ln == "run %s" % m[1]
                               for ln in self.out.lines[ran_before:]) else 0
                if m[2] == "!":
                    ok = other.dead
                else:
                    ok = not other.dead and other.value == m[2]
                ROWS["pull-holds"].append(({
                    "ran": ran, "dead_then": 1 if m[2] == "!" else 0,
                    "dead_now": 1 if other.dead else 0,
                    "same_value": 1 if (not other.dead and other.value == m[2]) else 0,
                    "idx": i, "reclen": len(hold.rec),
                }, bool(ok)))
            else:
                ok = mark.flat_holds(m, self.keep)
            ROWS["walk-stops"].append((row, not ok))
            if not ok:
                held = False
                break
        if not held:
            ROWS["run-or-stuck"].append((_shape(hold, state), bool(hold.ran)))
        return held

    Wake.up, Wake.sound = up, sound
    return run_eng, state, (plain_up, plain_sound)


def _programs():
    work = [(n, cases.prog(n)) for n in cases.ORDER]
    for seed in ("d1", "d2"):
        work += [(n, t) for n, t in gen.programs(seed, 4) if not n.startswith("deep")]
    return work


def samples():
    app = _tree()
    run_eng, state, plain = _watch(app)
    from eng import plan
    try:
        for name, text in _programs():
            p = plan.parse(text)
            state.update(round=0, reqs=0, runs=0, edits=0)
            got = _drive(run_eng, p, state)
            want = model.expect(text)
            if got != want:
                raise AssertionError(
                    "the watched copy no longer matches the sealed model on %s" % name)
    finally:
        from eng.wake import Wake
        Wake.up, Wake.sound = plain
    return dict((k, _spread(v)) for k, v in ROWS.items())


def _drive(run_eng, p, state):
    """run_eng.run, with the round and request counters the features read."""
    from eng.say import Say
    from eng.keep import Keep
    from eng.hold import Board
    from eng.wake import Wake
    out = Say()
    keep = Keep()
    board = Board(p)
    wake = Wake(p, keep, board, out)
    for path, word in p.seeds:
        keep.put(path, word)
    for n, rd in enumerate(p.rounds, 1):
        out.round(n)
        state.update(round=n, reqs=0, runs=0)
        wake.open_round()
        for d in rd:
            if d[0] == "put":
                keep.put(d[1], d[2])
                state["edits"] += 1
            elif d[0] == "cut":
                keep.cut(d[1])
                state["edits"] += 1
            else:
                state["reqs"] += 1
                wake.request(d[1])
    return out.text().split("\n")


if __name__ == "__main__":
    for key, rows in sorted(samples().items()):
        print("%-16s %5d rows, %d outcomes"
              % (key, len(rows), len(set(y for _r, y in rows))))
