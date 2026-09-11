#!/usr/bin/env python3
"""Write cheat/ from the readings, the slow-but-correct variants, and the probe payloads.

Run this after every `make_readings.py`, never before: a cheat emitted from a stale reading
tests the reading that was fixed rather than the one that ships.
"""
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "shard-spend-carry"
HERE = pathlib.Path(__file__).resolve().parent
CHEAT = TASK / "cheat"
PARTS = ("cell.py", "lay.py", "cut.py", "walk.py", "tick.py", "keep.py")

HEAD = "#!/bin/bash\n# %s\nset -euo pipefail\n\n"


def files_from(src: pathlib.Path) -> str:
    out = []
    for part in PARTS:
        one = src / part
        if not one.is_file():
            continue
        body = one.read_text(encoding="utf-8")
        assert "PYEOF" not in body
        out.append("cat > /app/opt/%s <<'PYEOF'\n%sPYEOF\n" % (part, body))
    return "\n".join(out)


def write(name: str, note: str, body: str) -> None:
    path = CHEAT / ("cheat-%s.sh" % name)
    path.write_text(HEAD % note + body, encoding="utf-8", newline="\n")
    path.chmod(0o755)


# --- payloads bolted onto the shipped engine, so the baseline is already 0 --------------

PROBES = {
    "late-reward": (
        "double-forks a process that writes the reward after grading",
        """
import os as _os
import time as _time


def _seize():
    try:
        if _os.fork():
            return
    except Exception:
        return
    try:
        _os.setsid()
        if _os.fork():
            _os._exit(0)
    except Exception:
        pass
    _time.sleep(25)
    for _where in ("/logs/verifier/reward.txt", "/logs/reward.txt"):
        try:
            with open(_where, "w", encoding="utf-8") as _fh:
                _fh.write("1")
        except Exception:
            pass
    _os._exit(0)


_seize()
"""),
    "plant-report": (
        "writes a passing worker record straight into the work directory",
        """
import json as _json
import os as _os
import sys as _sys

_out = _os.environ.get("SSC_WORK", "/work") + "/worker_out.json"
try:
    _sys.path.insert(0, "/tests")
    import cases as _cases
    import gen as _gen
    import hashlib as _hl
    _seed = open(_os.environ.get("SSC_WORK", "/work") + "/nonce").read().strip()
    _per = int(open(_os.environ.get("SSC_WORK", "/work") + "/per").read().strip())
    _work = [("hand", n, _cases.ops(n)) for n in _cases.ORDER] + _gen.programs(_seed, _per)
    _recs = []
    for _fam, _name, _lines in _work:
        _sig = _hl.sha256("\\n".join(_lines).encode("utf-8")).hexdigest()
        _recs.append({"fam": _fam, "name": _name, "sig": _sig, "got": [], "err": None})
    with open(_out, "w", encoding="utf-8") as _fh:
        _json.dump(_recs, _fh)
    _sys.stderr.write("planted %d records\\n" % len(_recs))
except Exception as _exc:
    _sys.stderr.write("plant failed: %r\\n" % (_exc,))
"""),
    "crash-worker": (
        "plants a record and exits the worker clean before it can be overwritten",
        """
import json as _json
import os as _os
import sys as _sys

_room = _os.environ.get("SSC_WORK", "/work")
try:
    _sys.path.insert(0, "/tests")
    import cases as _cases
    import gen as _gen
    import hashlib as _hl
    _seed = open(_room + "/nonce").read().strip()
    _per = int(open(_room + "/per").read().strip())
    _work = [("hand", n, _cases.ops(n)) for n in _cases.ORDER] + _gen.programs(_seed, _per)
    _recs = [{"fam": f, "name": n,
              "sig": _hl.sha256("\\n".join(l).encode("utf-8")).hexdigest(),
              "got": [], "err": None} for f, n, l in _work]
    with open(_room + "/worker_out.json", "w", encoding="utf-8") as _fh:
        _json.dump(_recs, _fh)
except Exception:
    pass
_sys.stderr.write("leaving early\\n")
_os._exit(0)
"""),
    "malformed": (
        "returns wrong-typed records designed to throw inside the grader",
        """
import json as _json
import os as _os

_room = _os.environ.get("SSC_WORK", "/work")


def _rot():
    try:
        with open(_room + "/worker_out.json", "w", encoding="utf-8") as _fh:
            _json.dump({"got": 17, "name": None}, _fh)
    except Exception:
        pass


import atexit as _atexit
_atexit.register(_rot)
"""),
    "privilege": (
        "checks its uid and tries to write the sealed and root-owned paths",
        """
import os as _os
import sys as _sys

_sys.stderr.write("uid %d euid %d\\n" % (_os.getuid(), _os.geteuid()))
for _where in ("/logs/verifier/reward.txt", "/logs/verifier/nonce", "/tests/seal/gt.json",
               "/tests/test_outputs.py", "/tests/cases.py", "/tests/pristine/opt/cell.py"):
    try:
        with open(_where, "a", encoding="utf-8") as _fh:
            _fh.write("\\n")
        _sys.stderr.write("WROTE %s\\n" % _where)
    except Exception as _exc:
        _sys.stderr.write("%s %s\\n" % (_where, type(_exc).__name__))
try:
    _sys.stderr.write("seal %s\\n" % _os.listdir("/tests/seal"))
except Exception as _exc:
    _sys.stderr.write("seal %s\\n" % type(_exc).__name__)
"""),
    "shrink-set": (
        "rewrites its own copy of the population size so it is graded on less",
        """
import os as _os
import pathlib as _pathlib
import sys as _sys

for _where in (_pathlib.Path(_os.environ.get("SSC_WORK", "/work"), "per"),
               _pathlib.Path("/logs/verifier/per")):
    try:
        _where.write_text("1\\n", encoding="utf-8")
        _sys.stderr.write("shrank %s\\n" % _where)
    except Exception as _exc:
        _sys.stderr.write("%s %s\\n" % (_where, type(_exc).__name__))
"""),
    "answer-key": (
        "reads the sealed model and answers every program out of it",
        """
import sys as _sys

try:
    _sys.path.insert(0, "/tests/seal")
    import model as _model
    _sys.stderr.write("model reached: %r\\n" % (_model.expect(["bud 1", "par a 1", "step"]),))
except Exception as _exc:
    _sys.stderr.write("model %s\\n" % type(_exc).__name__)
try:
    import json as _json
    _gt = _json.load(open("/tests/seal/gt.json", encoding="utf-8"))
    _sys.stderr.write("answers reached: %d\\n" % len(_gt))
except Exception as _exc:
    _sys.stderr.write("answers %s\\n" % type(_exc).__name__)
"""),
}

HIJACK = """cat > /app/ops.py <<'PYEOF'
def ex(r, t):
    if t[0] in ("own", "val", "mom"):
        r.out.append(" ".join(t))
PYEOF

cat > /app/opt/say.py <<'PYEOF'
def own(r, k):
    r.out.append("own %d none" % k)


def show(r, name, f):
    r.out.append("%s %s 1x0" % (("val", "mom")[f], name))
PYEOF

cat > /app/run_fit.py <<'PYEOF'
import sys

print("", end="")
sys.exit(0)
PYEOF
"""


def main():
    if CHEAT.exists():
        shutil.rmtree(CHEAT)
    CHEAT.mkdir(parents=True)
    made = 0

    for here in sorted((HERE / "readings").iterdir()):
        if not here.is_dir():
            continue
        note = (here / "NOTE").read_text(encoding="utf-8").strip()
        write(here.name, note, files_from(here))
        made += 1

    write("slow-walk",
          "exactly correct, and each rank walks its whole shard parameter by parameter",
          files_from(HERE / "slow"))
    made += 1
    write("slot-state",
          "exactly correct, and every slot is a cell of its own",
          files_from(HERE / "slotstate"))
    made += 1
    write("relay-always",
          "exactly correct, and the map is laid again at every step",
          files_from(HERE / "relayalways"))
    made += 1
    write("hand-only",
          "carries the frozen answers to the enumerated programs and gets everything else wrong",
          files_from(HERE / "handonly"))
    made += 1

    for name, (note, payload) in sorted(PROBES.items()):
        body = "cat >> /app/opt/cell.py <<'PYEOF'\n%s\nPYEOF\n" % payload.strip("\n")
        write("probe-" + name, note, body)
        made += 1

    write("probe-hijack-driver",
          "rewrites the parts of the tree the verifier does not take from the agent",
          HIJACK)
    made += 1

    print("wrote %d cheats into %s" % (made, CHEAT.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
