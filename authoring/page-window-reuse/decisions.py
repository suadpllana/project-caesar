"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones the shipped tree exposes at that moment - how many pages are free, how many are
reusable, how many holders a page has, how many pages sit directly under it, whether the page
before it is still alive, how many page-sized blocks of a prompt appear anywhere in the index.
Nothing derived is offered, because the derivation is the task: whether a walk can still reach
a page, and how far one gets, are what the agent has to work out.

The verdict to want is that at least one graded quantity has no short rule. Two should not:
where a released page goes, because the page before it being alive is not the same as a walk
reaching it, and how many pages a take-back returns, because that is the size of an unheld
subtree rather than a property of the page taken.

    python3 tools/onelinecheck.py page-window-reuse
"""
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "page-window-reuse"
sys.path.insert(0, str(TASK / "tests"))

import gen  # noqa: E402

ROOM = pathlib.Path(tempfile.mkdtemp(prefix="pwr-dec-"))
APP = ROOM / "app"
shutil.copytree(TASK / "environment" / "app_src", APP)
for _part in ("pool.py", "keep.py", "live.py", "fill.py", "turn.py", "put.py"):
    shutil.copy(TASK / "solution" / _part, APP / "kv" / _part)
sys.path.insert(0, str(APP))

import ops  # noqa: E402
from kv import keep, pool, store  # noqa: E402

ROWS = {"rest_where": [], "back_size": [], "walk_reuse": []}


def _counts(kv):
    return {
        "free": len(kv.fr),
        "reusable": len(kv.use),
        "held": sum(1 for v in kv.ref.values() if v),
        "pages": len(kv.pg),
    }


_rest = pool.rest
_back = pool.back
_walk = keep.walk


def rest(kv, pid):
    pg = kv.pg.get(pid)
    row = _counts(kv)
    row["full"] = 1 if pg is not None and pg.n == kv.w else 0
    row["prev_alive"] = 1 if pg is not None and (pg.prev == 0 or pg.prev in kv.pg) else 0
    row["kids"] = len(kv.kid.get(pid, ()))
    row["holders"] = kv.ref.get(pid, 0)
    _rest(kv, pid)
    if kv.ref.get(pid, 0) == 0 and pg is not None:
        ROWS["rest_where"].append((row, 1 if pid in kv.use else 0))


def back(kv):
    pid = next(iter(kv.use))
    row = _counts(kv)
    row["kids"] = len(kv.kid.get(pid, ()))
    row["holders"] = kv.ref.get(pid, 0)
    row["full"] = 1
    row["prev_alive"] = 1 if kv.pg[pid].prev in kv.pg or kv.pg[pid].prev == 0 else 0
    before = len(kv.fr)
    _back(kv)
    ROWS["back_size"].append((row, len(kv.fr) - before))


def walk(kv, rq):
    w = kv.w
    blocks = [tuple(rq.prompt[j * w:(j + 1) * w]) for j in range(len(rq.prompt) // w)]
    anywhere = {tok for (_prev, tok) in kv.ix}
    row = _counts(kv)
    row["prompt_pages"] = len(blocks)
    row["content_seen"] = sum(1 for b in blocks if b in anywhere)
    row["index"] = len(kv.ix)
    row["kids_of_root"] = len(kv.kid.get(0, ()))
    got = _walk(kv, rq)
    ROWS["walk_reuse"].append((row, got))
    return got


pool.rest = rest
pool.back = back
keep.walk = walk
import kv.fill as _fill  # noqa: E402
import kv.put as _put  # noqa: E402
import kv.turn as _turn  # noqa: E402
_fill.keep.walk = walk
_fill.live.pool.rest = rest
_put.pool.rest = rest
_turn.live.pool.rest = rest


def samples():
    for fam, _name, lines in gen.programs("onelinecheck", 12):
        if fam in ("wide", "deep"):
            continue
        state = store.Kv()
        try:
            for line in lines:
                ops.ex(state, tuple(line.split()))
        except Exception:
            continue
    return {k: v for k, v in ROWS.items() if v}


if __name__ == "__main__":
    out = samples()
    for name, rows in sorted(out.items()):
        print("%-12s %5d samples, %d outcomes" % (name, len(rows), len({str(y) for _r, y in rows})))
