"""The graded decisions as rows of features the agent can read at the moment they are made.

`tools/onelinecheck.py` searches these for the shortest exact rule. Three decisions are recorded
from the reference itself, wrapped rather than copied, and the wrapped reader is asserted to print
the sealed model's log on every page it is run on, so the rows cannot come from a reader that
drifted:

  cut    at the cut step of a tick in which a polite utterance is still playing: does it get cut
  unit   for the difference the reader has just chosen: is it spoken as an atomic unit
  held   whenever a difference is put in the line: is it held

The features are what the page and the tick's records show at that moment, plus what any reader
knows about its own speech: counts of touched text in assertive regions, busy and atomic
attributes on the node's current parent and on its region element, how deep the node sits, and
whether it is still exposed in the region. Nothing says what the listener believes, what the
playing utterance carries or which parent a removed node was last believed under, because the
shipped tree has none of that and building it is the task.

The verdict to want is that none of the three has a short rule. `held` and `unit` should not,
because an element between the parent and the region can decide either, and a removal is decided
from the parent it had when it was last believed, not from where it is. `cut` should not, because
an edit that restores the believed words cuts nothing and a difference released by an inner busy
element cuts without any assertive text being touched.

    python3 tools/onelinecheck.py live-region-reader
"""
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.join(os.path.dirname(os.path.dirname(HERE)), "tasks", "live-region-reader")
PARTS = ("look.py", "know.py", "watch.py", "unit.py", "line.py", "voice.py")
PER = 20

sys.path.insert(0, os.path.join(TASK, "tests"))
sys.path.insert(0, os.path.join(TASK, "tests", "seal"))
import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

ROWS = {"cut": [], "unit": [], "held": []}


def _reference():
    room = tempfile.mkdtemp(prefix="lrr-decisions-")
    app = os.path.join(room, "app")
    shutil.copytree(os.path.join(TASK, "environment", "app_src"), app)
    for f in PARTS:
        shutil.copy(os.path.join(TASK, "solution", f), os.path.join(app, "sr", f))
    sys.path.insert(0, app)
    import run_sr
    from sr import line, look, unit, voice
    return run_sr, line, look, unit, voice


def _atomic(pg, e):
    v = pg.attr(e, "aria-atomic") if e is not None else None
    return {"true": 2, "false": 1}.get(v, 0)


def _busy(pg, e):
    return int(e is not None and pg.attr(e, "aria-busy") == "true")


def _depth(pg, x, r):
    d = 0
    while x is not None and x != r:
        d += 1
        x = pg.up(x)
    return d if x == r else -1


def _shape(pg, look, r, n):
    shown, reg = look.place(pg, n)
    p = pg.up(n)
    return {
        "removal": int(not (shown and reg == r)),
        "attached": int(pg.attached(n)),
        "depth": _depth(pg, p, r),
        "busy_parent": _busy(pg, p),
        "busy_region": _busy(pg, r),
        "atomic_parent": _atomic(pg, p),
        "atomic_region": _atomic(pg, r),
    }


def _touched(pg, recs):
    out = set()
    for rec in recs:
        if rec[0] == "text":
            out.add(rec[1])
        elif rec[0] in ("add", "move"):
            out.update(x for x in pg.walk(rec[1]) if pg.is_text(x))
    return out


def _watch(line, look, unit, voice):
    pick, put, step = voice.Reader._pick, line.Line.put, voice.Reader.step

    def watched_pick(self):
        k = pick(self)
        if k is not None:
            r, n = k
            rr, cur = self.watch.now(n)
            c = cur if rr == r else None
            ROWS["unit"].append((_shape(self.pg, look, r, n),
                                 unit.unit(self.pg, self.know, k, c) is not None))
        return k

    def watched_put(self, k, age, cls, held, anchor):
        pg = self.page
        ROWS["held"].append((_shape(pg, look, k[0], k[1]), bool(held)))
        return put(self, k, age, cls, held, anchor)

    def watched_step(self, t, recs):
        self.line.page = self.pg
        playing = self.play is not None and self.play[0] == "polite" and self.play[1] != t
        feats = None
        if playing:
            pg = self.pg
            loud = 0
            for x in _touched(pg, recs):
                shown, reg = look.place(pg, x)
                if shown and reg is not None and look.loudness(pg, reg) == "assertive":
                    loud += 1
            busy = sum(1 for r in {look.region(pg, x) for x in _touched(pg, recs)}
                       if r is not None and _busy(pg, r))
            feats = {
                "assertive_touched": loud,
                "assertive_busy": busy,
                "busy_released": sum(1 for rec in recs if rec[0] in ("set", "unset")
                                     and rec[2] == "aria-busy" and not _busy(pg, rec[1])),
                "drops": sum(1 for rec in recs if rec[0] == "drop"),
                "left": self.play[1] - t,
            }
        out = step(self, t, recs)
        if feats is not None:
            ROWS["cut"].append((feats, any(x.endswith(" cut") for x in out)))
        return out

    voice.Reader._pick = watched_pick
    line.Line.put = watched_put
    voice.Reader.step = watched_step


def samples():
    run_sr, line, look, unit, voice = _reference()
    _watch(line, look, unit, voice)
    pages = [cases.prog(n) for n in cases.ORDER]
    for fam, big in gen.FAMILIES:
        if not big:
            pages += [gen.one("decisions", fam, i) for i in range(PER)]
    for lines in pages:
        got = run_sr.run("\n".join(lines) + "\n")
        if got != model.expect(lines):
            raise AssertionError("the wrapped reference drifted from the model")
    return ROWS


if __name__ == "__main__":
    for name, rows in samples().items():
        print(name, len(rows), sum(1 for _r, y in rows if y))
