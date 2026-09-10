"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features offered are
the raw ones the tree exposes at that moment, plus the two tempting derivations a first plan
reaches for - the start of the lowest free range that is large enough, and what would be left of
that range after the request - because a rule that fits either of those is a rule an agent writes
cold, and the point of measuring is to find out whether one does.

The verdict to want is that at least one graded quantity has no short rule. Two should not: where
a range is placed, because the answer is the lowest address inside a part rather than the lowest
range that fits and because the aside list can answer first; and how large it comes out, because
the leftover goes to the range only under sixteen bytes and is otherwise left alone, which is a
conditional rather than a comparison. Which of the two paths a freed range takes is a stated
threshold and is conceptually the shortest rule here; the search reports no rule for it only
because its constants stop at three and cannot express two hundred and fifty-six. Read that row
as measured-not-expressible rather than as depth.

    python3 authoring/aside-fit-sweep/decisions.py
"""
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TASK = ROOT / "tasks" / "aside-fit-sweep"
PARTS = ("find.py", "cut.py", "side.py", "back.py", "edge.py")

_room = pathlib.Path(tempfile.mkdtemp(prefix="afs-dec-"))
_app = _room / "app"
shutil.copytree(TASK / "environment" / "app_src", _app)
for _p in PARTS:
    shutil.copy(TASK / "solution" / _p, _app / "pool" / _p)
sys.path.insert(0, str(_app))
sys.path.insert(0, str(TASK / "tests"))

import gen  # noqa: E402
import ops  # noqa: E402
from pool import find, side  # noqa: E402
from reg import geom, live, text  # noqa: E402

KIND = {"same": 1, "at": 2, "no": 3}


def _runs(h):
    m = find._map(h)
    return [(s, sz) for lst in m.runs for s, sz in lst]


def _aside(h):
    held, _by, _tick = side._bag(h)
    return list(held.values())


def _first_fit(h, n):
    """The lowest free range large enough - the answer a first plan gives."""
    for s, sz in _runs(h):
        if sz >= n:
            return s, sz
    return -1, -1


def _state(h, n):
    runs = _runs(h)
    aside = _aside(h)
    fit_at, fit_size = _first_fit(h, n)
    return {
        "want": n,
        "free_runs": len(runs),
        "free_bytes": sum(sz for _s, sz in runs),
        "first_run_at": runs[0][0] if runs else -1,
        "first_run_size": runs[0][1] if runs else -1,
        "first_fit_at": fit_at,
        "first_fit_size": fit_size,
        "first_fit_left": fit_size - n if fit_size >= 0 else -1,
        "aside_held": len(aside),
        "aside_exact": sum(1 for _a, sz in aside if sz == n),
        "aside_bytes": sum(sz for _a, sz in aside),
        "live_ranges": sum(1 for r in h.ids.values() if r.live),
    }


def samples():
    place_at, place_size, fit_kind, back_where = [], [], [], []
    for fam, _name, lines in gen.programs("decisions", 6):
        if fam in ("wide", "churn"):
            continue
        span, part, body = text.parse(lines)
        h = live.Pool(span, part)
        acc = []
        for line in body:
            bits = tuple(line.split())
            mark = len(acc)

            if bits[0] == "get":
                rec = h.ids.get(bits[1])
                if rec is not None and rec.live:
                    ops.ex(h, bits, acc)
                    continue
                n = geom.up(int(bits[2]))
                if not geom.ok(h, n):
                    ops.ex(h, bits, acc)
                    continue
                row = _state(h, n)
                ops.ex(h, bits, acc)
                made = acc[mark:]
                if made and made[0].startswith("at "):
                    got = made[0].split()
                    place_at.append((row, int(got[2])))
                    place_size.append((dict(row), int(got[3]) - n))
                continue

            if bits[0] == "fit":
                rec = h.ids.get(bits[1])
                if rec is None or not rec.live:
                    ops.ex(h, bits, acc)
                    continue
                n = geom.up(int(bits[2]))
                row = _state(h, n)
                row["have_now"] = rec.size
                row["room_in_part"] = geom.part_end(h, rec.at) - rec.at
                row["free_after"] = find.after(h, rec.at, rec.size)
                ops.ex(h, bits, acc)
                made = acc[mark:]
                fit_kind.append((row, KIND.get(made[0].split()[0], 0) if made else 0))
                continue

            if bits[0] == "put":
                rec = h.ids.get(bits[1])
                if rec is None or not rec.live:
                    ops.ex(h, bits, acc)
                    continue
                before = len(_aside(h))
                row = _state(h, rec.size)
                row["giving_back"] = rec.size
                ops.ex(h, bits, acc)
                back_where.append((row, int(len(_aside(h)) > before)))
                continue

            ops.ex(h, bits, acc)

    return {
        "where a range is placed": place_at,
        "how much larger than asked": place_size,
        "what a resize does": fit_kind,
        "aside or into the map": back_where,
    }


if __name__ == "__main__":
    for name, rows in samples().items():
        outcomes = len({str(y) for _r, y in rows})
        print("%-28s %5d samples, %d outcomes" % (name, len(rows), outcomes))
