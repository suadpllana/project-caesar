"""The wrong readings as the files they replace in the reference, for tools/readingcheck.py.

Each reading is built by emit.py, so the cheats that ship under cheat/ and the readings measured
here are the same six files and cannot drift apart. The builders are run with emit's writer
swapped for a collector, so measuring touches nothing on disk. switches.py holds the same
readings as switches on a plain stepper, for sweeping a whole population quickly.

    python3 tools/readingcheck.py stale-line-spin [rounds]
"""
import os
import pathlib
import shutil
import signal
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "stale-line-spin"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))
import cases  # noqa: E402
import emit  # noqa: E402
import gen  # noqa: E402

REFERENCE = str(TASK / "solution")

EDITS = {
    "coherent": "every load and every sum answers from global memory",
    "per-block-cache": "a cache per block, gone when the block exits",
    "store-broadcast": "a store updates every multiprocessor's cached copy",
    "store-leaves-copy": "a store leaves the storer's own cached copy as it was",
    "store-allocates": "a store that misses fills the line",
    "atom-updates-own": "an atomic updates the issuer's cached copy",
    "lru": "a hit moves its line to the back of the replacement order",
    "cg-keeps": "a bypassing load or sum leaves the cached line alone",
    "cg-drops-all": "a bypassing load drops the line from every multiprocessor",
    "fence-all": "a fence empties every multiprocessor's cache",
    "fence-noop": "a fence does nothing",
    "line-word": "a line is a single word",
    "sum-one-issue": "a sum reads its n lines from global memory in one issue",
    "sum-coherent": "a cached sum reads every line from global memory and fills nothing",
    "sum-no-fill": "a cached sum uses a line it finds cached but fills none it misses",
    "sum-cg-keeps": "a bypassing sum leaves a cached line where it is",
    "sum-word-issues": "a sum reads 4n words from its address, one word per issue",
    "sum-first-issue": "a sum reads all its lines at its first issue and waits out the rest",
    "sum-last-issue": "a sum takes its n issues and reads all its lines at the last one",
    "sum-fills-at-end": "a cached sum fills the lines it missed only when it finishes",
    "sum-is-spin": "a block in the middle of a sum counts as sitting at a spin",
    "lane-late-read": "a sum carried forward reads each line as memory holds it when the "
                      "stretch is settled",
    "lane-same-cycle": "a store never reaches a sum or bypassing spinner carried forward on"
                       " another multiprocessor in the cycle it is made",
    "place-mod": "block b goes to multiprocessor b mod S and waits for a slot there",
    "place-first-free": "a block goes to the lowest-numbered multiprocessor with room",
    "free-same-cycle": "an exit frees its slot in the same cycle",
    "placed-next-cycle": "a placed block first issues on the next cycle",
    "rotate-from-zero": "each cycle the scan starts again from slot 0",
    "sm-reverse": "multiprocessors issue in descending order",
    "work-plus-one": "work of v cycles makes the block ready at t+v+1",
    "lt-inclusive": "lt holds when the loaded value is at most v",
    "cmp-reversed": "a spin compares v against the loaded value",
    "park-spinners": "a failing spinner leaves the rotation until its word is stored to",
    "skip-any-spin": "time is skipped whenever every ready block is failing a spin",
    "skip-no-rotate": "a stretch carried forward leaves the rotation where it was",
    "hang-no-store": "a hang is called as soon as every block spins and no attempt passes",
    "hang-at-detect": "a hang is reported at the cycle it is recognised",
    "hang-last-start": "a hang is dated from the cycle it is found, never from its start",
}

_BUILT = {}


def _collect(name, comment, files, reading=True, extra=None):
    if reading:
        _BUILT[name] = dict(files)


emit.write = _collect
for _build in emit.READING_BUILDERS:
    _build()
READINGS = dict(_BUILT)
assert set(READINGS) == set(EDITS), sorted(set(READINGS) ^ set(EDITS))

LIMIT = 30          # seconds for one launch; a reading that starves a block never finishes
_TREES = {}
_SEEN = {}


class _Late(Exception):
    pass


def _alarm(signum, frame):
    raise _Late()


def _tree(policy):
    key = str(policy)
    if key not in _TREES:
        app = os.path.join(tempfile.mkdtemp(prefix="sls-read-"), "app")
        shutil.copytree(TASK / "environment" / "app_src", app)
        for part in emit.PARTS:
            src = os.path.join(key, part)
            if os.path.isfile(src):
                shutil.copyfile(src, os.path.join(app, "sim", part))
        _TREES[key] = app
    return _TREES[key]


def run(policy, text):
    """The runner's lines for one launch under one directory of the six files."""
    key = (str(policy), text)
    if key in _SEEN:
        return _SEEN[key]
    app = _tree(policy)
    for name in [m for m in sys.modules if m in ("sim", "run_launch") or m.startswith("sim.")]:
        del sys.modules[name]
    sys.path.insert(0, app)
    old = signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(LIMIT)
    try:
        import run_launch
        got = run_launch.run(text.rstrip("\n") + "\n")
    except _Late:
        got = ["TIMEOUT"]
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)
        sys.path.remove(app)
    _SEEN[key] = got
    return got


def enumerated():
    return [(name, "\n".join(cases.prog(name))) for name in cases.ORDER]


def generated(n):
    per = max(1, n // 8)
    return [(name, "\n".join(lines)) for fam, name, lines in gen.programs("readingcheck", per)
            if fam not in ("wide", "deep", "stream")]
