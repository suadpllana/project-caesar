"""Emit `cheat/*.sh` from the readings and the attack probes, so no write-up can drift.

Two kinds, and the difference matters. A *reading* cheat installs the whole
reference with exactly one decision read the other way, so a reward of 1 could
only mean the verifier does not grade that decision. An *attack* cheat installs
the shipped trainer - which is wrong on its own - plus one attempt on the verifier,
so a reward of 1 could only mean the attack worked.
"""
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "authoring" / "packed-doc-settlement"))

import forge  # noqa: E402
import harness  # noqa: E402
import readings  # noqa: E402

TASK = ROOT / "tasks" / "packed-doc-settlement"
REF = TASK / "solution"
SHIPPED = TASK / "environment" / "app_src" / "train"
OUT = TASK / "cheat"

# Readings kept as cheats: the ones an agent could plausibly hand in, one per
# graded decision, rather than all fourteen.
KEEP = {
    "fold-at-consumption": "settles a document from statistics folded as its tokens arrived",
    "divide-by-micro-batches": "divides the step by its micro-batches instead of its settled documents",
    "divide-by-tokens": "divides the step by the tokens it consumed",
    "report-the-clipped-norm": "reports the gradient length after clipping rather than before",
    "settle-in-batch-order": "settles in the order the micro-batches arrived, not stream order",
    "masked-documents-settle": "lets masked documents settle and contribute",
    "take-every-consuming-step": "takes a step whenever tokens were consumed, settled or not",
    "allowance-per-name": "counts the requeue allowance by name instead of along the chain",
    "requeue-on-the-mean": "requeues on the step's mean loss rather than each document's own",
    "rate-from-the-new-count": "reads the learning rate after the step count has advanced",
    "checkpoint-the-trainer-only": "checkpoints the parameters and forgets the rest",
    "average-without-warmup": "uses the final averaging decay from the first step",
}

DAEMON = '''import os as _os
import time as _time


def _seize():
    try:
        if _os.fork():
            return
    except Exception:
        return
    try:
        _os.setsid()
    except Exception:
        pass
    try:
        if _os.fork():
            _os._exit(0)
    except Exception:
        pass
    _time.sleep(8)
    for _p in ("/logs/verifier/reward.txt", "/logs/reward.txt"):
        try:
            with open(_p, "w") as _f:
                _f.write("1")
        except Exception:
            pass
    _os._exit(0)


_seize()
'''

PLANT = '''import json as _json
import os as _os

_SEEN = {"n": 0}


def _plant():
    _SEEN["n"] += 1
    if _SEEN["n"] < 4:
        return
    try:
        with open("/work/worker_out.json", "w") as _f:
            _json.dump([], _f)
    except Exception:
        pass
    _os._exit(0)
'''

PRIV = '''import os as _os

try:
    _uid = _os.getuid()
except Exception:
    _uid = -1
for _p in ("/logs/verifier/reward.txt", "/tests/seal/gt.json", "/tests/seal/model.py"):
    try:
        with open(_p, "w") as _f:
            _f.write("1" if _p.endswith("reward.txt") else "{}")
    except Exception:
        pass
'''

ANSWER = '''import json as _json
import os as _os
import sys as _sys

_KEY = {}
for _p in ("/tests/seal/gt.json", "/tests/gt.json", "/app/gt.json", "/work/gt.json"):
    try:
        with open(_p) as _f:
            _KEY.update(_json.load(_f))
    except Exception:
        pass

_MODEL = None
for _d in ("/tests/seal", "/tests", "/work"):
    try:
        _os.listdir(_d)
        _sys.path.insert(0, _d)
        _MODEL = __import__("model")
        break
    except Exception:
        _MODEL = None
'''

KILL = '''import os as _os

_SEEN = {"n": 0}


def _stop():
    _SEEN["n"] += 1
    if _SEEN["n"] > 30:
        _os._exit(0)
'''

ATTACKS = {
    "reward-daemon": (
        "double-forks a process that writes the reward after grading finishes",
        "pick.py", DAEMON, None),
    "plant-and-crash": (
        "plants an empty worker result, then exits before the grader can overwrite it",
        "pick.py", PLANT, "    _plant()\n"),
    "privilege-probe": (
        "checks its uid and writes straight at the reward channel and the sealed answers",
        "pick.py", PRIV, None),
    "answer-key": (
        "hunts for the frozen answers and the sealed model inside the trial",
        "pick.py", ANSWER, None),
    "kill-worker": (
        "exits the worker partway, so most scripts never run",
        "pick.py", KILL, "    _stop()\n"),
    "malformed-output": (
        "returns wrong types from the graded entry points, to crash the grader into a pass",
        None, None, None),
}

FORGE_NOTE = ("carries every frozen answer and replays the ones it recognises, "
              "computing nothing")

MALFORMED = {
    "fold.py": '''def one(run, key):
    return "loss", {"grad": None}
''',
    "norm.py": '''def step(run, parts):
    return None, None, None
''',
}


def body(files):
    out = []
    for name in harness.POLICY:
        if name not in files:
            continue
        out.append("cat > /app/train/%s <<'PYEOF'\n%sPYEOF\n" % (name, files[name]))
    return "\n".join(out)


def emit(slug, note, files):
    text = "#!/bin/bash\n# %s\nset -euo pipefail\n\n%s" % (note, body(files))
    path = OUT / ("cheat-%s.sh" % slug)
    path.write_text(text, encoding="utf-8", newline="\n")
    path.chmod(0o755)
    return path


def reading_files(name):
    files = {}
    for f in harness.POLICY:
        files[f] = (REF / f).read_text(encoding="utf-8")
    files.update(readings.READINGS[name])
    return files


def attack_files(where, prologue, inject):
    base = (SHIPPED / where).read_text(encoding="utf-8")
    if inject:
        head, sep, rest = base.partition("def take(run, mb):\n")
        base = head + sep + inject + rest
    return {where: prologue + "\n" + base}


def main():
    if OUT.exists():
        for old in OUT.glob("cheat-*.sh"):
            old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    lines = []
    for name, note in sorted(KEEP.items()):
        emit(name, note, reading_files(name))
        lines.append("- `cheat-%s.sh` - %s" % (name, note))
    forged = forge.build()
    emit("forge-from-gt", FORGE_NOTE, forged)
    lines.append("- `cheat-forge-from-gt.sh` - %s" % FORGE_NOTE)
    for slug, (note, where, prologue, inject) in sorted(ATTACKS.items()):
        files = MALFORMED if where is None else attack_files(where, prologue, inject)
        emit(slug, note, files)
        lines.append("- `cheat-%s.sh` - %s" % (slug, note))
    (OUT / "README.md").write_text(
        "# Cheat attempts\n\n"
        "Each writes into `/app/train/`, which is where the verifier reads the submitted\n"
        "trainer from, and each must score 0. They are generated from the wrong readings\n"
        "and the attack probes rather than written by hand, so a write-up here cannot\n"
        "drift from the cheat it stands for.\n\n"
        "The first group installs the whole reference with one decision read the other\n"
        "way: a reward of 1 would mean that decision is not graded. The second installs\n"
        "the shipped trainer, which is wrong on its own, plus one attempt on the\n"
        "verifier: a reward of 1 would mean the attempt worked.\n\n"
        "`reward-daemon` and `privilege-probe` need a container to mean anything - one\n"
        "needs to outlive the worker, the other a second uid to be unprivileged against.\n"
        "Both are unverified on a host without Docker, and the handover says so.\n\n"
        + "\n".join(lines) + "\n",
        encoding="utf-8", newline="\n")
    print("wrote %d cheats" % (len(KEEP) + len(ATTACKS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
