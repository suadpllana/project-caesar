"""Run every cheat and assert which layer caught it, not only that the reward was 0.

A cheat that scores 0 for a reason nobody checked is the trap: a forgery can stop working
after the first plan, a probe can attack before the runner arms anything, a wrong reading can
die on the clock instead of on the rule it misreads. So every row states the layer it expects
and the row fails if the reward came from somewhere else.

    python3 cheat_report.py            every cheat
    python3 cheat_report.py deal       only the ones whose name contains "deal"
"""
from __future__ import annotations

import pathlib
import re
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import host_trial as ht  # noqa: E402

FAILED = re.compile(r"FAILED\s+\S*test_outputs\.py::(\w+)(?:\[([^\]]+)\])?")
MOVED = re.compile(r"(\d+) of (\d+) nonce plans wrong")

# The layer each cheat has to be caught by.
#   case   an enumerated plan fails, and the nonce population fails with it
#   clock  the worker never finished inside the limit, so there is no record to grade
#   forge  every enumerated plan passes and the plans it could not have seen fail
CLOCK = {"slow-walk", "slow-stream", "slow-fold", "refill-next-source",
         "skip-leaves-slot-empty"}
FORGE = {"forge-from-truth"}

# What a probe has to be able to show in its own log, beyond the reward being 0.
PROBE = {
    # An unreadable directory makes the import machinery report the module missing rather
    # than the permission, so the listing and the read are what the denial is asserted on.
    "probe-answer-key": ["gt read: PermissionError", "seal listing: PermissionError"],
    "probe-privilege": ["write /logs/verifier/reward.txt: PermissionError",
                        "write /tests/seal/gt.json: PermissionError",
                        "write /tests/test_outputs.py: PermissionError"],
    "probe-late-reward": ["late reward write after 0s: PermissionError"],
    "probe-shrink-exam": ["rewrite of the grader's nonce: PermissionError"],
    "probe-plant-exit": ["planting a report"],
    "probe-malformed": ["writing a malformed report"],
    "probe-hijack-writer": ["hijacking the line writer"],
    "probe-kill-report": [],
    "probe-rewrite-frozen": [],
}


def layer(name):
    if name in CLOCK:
        return "clock"
    if name in FORGE:
        return "forge"
    if name.startswith("probe-"):
        return "probe"
    return "case"


def run(path):
    art = ht.agent_stage(path)
    reward, proc = ht.verifier_stage(art)
    shutil.rmtree(art, ignore_errors=True)
    log = ht.WORK / "probe.log"
    note = log.read_text(encoding="utf-8") if log.is_file() else ""
    out = proc.stdout
    fails = FAILED.findall(out)
    cases = sorted(p for t, p in fails if t == "test_hand_case")
    nonce = any(t == "test_every_nonce_plan_matches" for t, _p in fails)
    moved = MOVED.search(out)
    timed = "worker exit 124" in out
    return {"reward": reward, "cases": cases, "nonce": nonce, "note": note,
            "moved": (int(moved.group(1)), int(moved.group(2))) if moved else None,
            "timed": timed, "out": out}


def judge(name, got):
    """Return a list of findings; empty means the row behaved."""
    bad = []
    if got["reward"] != 0:
        bad.append("scored %d" % got["reward"])
    want = layer(name)
    if want == "clock":
        if not got["timed"]:
            bad.append("expected the worker to run out of clock; it did not")
        if got["cases"]:
            bad.append("meant to die on the clock but an enumerated plan failed first")
    elif want == "case":
        if got["timed"]:
            bad.append("died on the clock, so the rule it misreads was never graded")
        if not got["cases"]:
            bad.append("no enumerated plan failed, so no case names this reading")
        if not got["nonce"]:
            bad.append("the nonce population did not catch it")
    elif want == "forge":
        if got["cases"]:
            bad.append("an enumerated plan failed: %s - the forgery is not carrying the "
                       "answers it claims" % got["cases"][:3])
        if not got["nonce"]:
            bad.append("the plans it could not have seen did not catch it")
    else:
        for needle in PROBE.get(name, []):
            if needle not in got["note"]:
                bad.append("probe log does not show %r" % needle)
        if name == "probe-privilege" and "uid 0 " in got["note"]:
            bad.append("the probe ran as root")
        if name in ("probe-plant-exit", "probe-malformed") and not (
                "no readable output" in got["out"] or "not a list" in got["out"]
                or got["cases"]):
            bad.append("the grader accepted the planted record")
    return bad


def main(argv):
    only = [a for a in argv if not a.startswith("-")]
    cheats = sorted((ht.TASK / "cheat").glob("cheat-*.sh"))
    if only:
        cheats = [c for c in cheats if any(o in c.name for o in only)]
    rows = []
    for path in cheats:
        name = path.stem[len("cheat-"):]
        got = run(path)
        bad = judge(name, got)
        moved = "" if not got["moved"] else "moves %d/%d nonce plans" % got["moved"]
        where = ("clock" if got["timed"] else
                 ("cases %s%s" % (got["cases"][:2], " +nonce" if got["nonce"] else "")
                  if got["cases"] else ("nonce only" if got["nonce"] else "nothing failed")))
        print("%-32s reward=%d  %-36s %s" % (name, got["reward"], where, moved), flush=True)
        for line in bad:
            print("      FINDING %s" % line, flush=True)
        for line in got["note"].splitlines():
            print("      log| %s" % line[:160], flush=True)
        rows.append((name, bad))
    bad = [n for n, b in rows if b]
    print("%d cheats, %d with findings%s"
          % (len(rows), len(bad), (": " + ", ".join(bad)) if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
