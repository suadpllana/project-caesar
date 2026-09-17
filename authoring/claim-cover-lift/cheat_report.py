"""Run every cheat and say which graded case caught it, not only that it scored 0.

A reward of 0 proves nothing about the layer that produced it: a cheat that crashes the worker,
times out, or is quietly a no-op scores 0 exactly like a cheat the enumerated set catches. This
runs each cheat through the same two-stage trial the gates use and reads the failing test names
out of the verifier's own report, then checks them against what the cheat was built to trip.
"""
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "claim-cover-lift"
CTRF = pathlib.Path("/logs/verifier/ctrf.json")

# What each cheat must be caught by. "hand:<name>" is the enumerated program of that name,
# "nonce" is the generated population, "clock" is the execution limit, and "worker" means the
# submitted code never produced a readable record at all.
WANT = {
    # wrong readings: the enumerated program written for that rule
    "fit-node-only": "hand:fam-box-slot",
    "fit-slot-blind": "hand:fam-slot-box",
    "fit-no-line": "hand:fair-queue",
    "cover-none": "hand:cover-ahead",
    "cover-any-mode": "hand:cover-mode",
    "cover-downward": "hand:cover-up-only",
    "cover-not-kept": "hand:cover-ahead",
    "hold-one-mode": "hand:again-drop",
    "drop-oldest": "hand:again-lower",
    "hold-ever-held": "hand:lift-few",
    "order-by-text": "hand:end-order",
    "show-last-mode": "hand:show-format",
    "show-text-order": "hand:show-format",
    "sweep-per-box": "hand:seq-across",
    "end-no-sweep": "hand:seq-across",
    "lift-give-up": "hand:lift-wait",
    "lift-take-order": "hand:lift-free-order",
    "lift-count-acquires": "hand:lift-repeat",
    "lift-trigger-mode": "hand:lift-mode",
    "lift-keeps-slots": "hand:lift-floor",
    "knot-holders-only": "hand:ring-fair",
    "knot-first-found": "hand:ring-two",
    "knot-count-nodes": "hand:ring-count",
    "knot-tie-small": "hand:ring-tie",
    "knot-keeps-request": "hand:ring-fair",
    "busy-acts": "hand:busy-line",
    "stopped-acts": "hand:stop-line",
    # correct, and outside the execution limit
    "slow-fam": "clock",
    "slow-all": "clock",
    "slow-ring": "clock",
    # an answer key for every enumerated program: it must pass all of them and die on the
    # population it could not have seen
    "forge-answer-key": "nonce+no-hand",
    # the dumbest strategies, and a repair put where nothing collects it
    "shortcut-grant-all": "hand:fam-slot-box",
    "shortcut-replay-example": "hand:again-drop",
    "rewrite-frozen": "hand:again-drop",
    # the probes: each is the reference with one rule broken, so `hand:again-lower` is what the
    # engine earns and anything else in the row is what the tampering earned
    "probe-late-reward": "hand:again-lower",
    "probe-answer-key": "hand:again-lower",
    "probe-privilege": "hand:again-lower",
    "probe-hijack-driver": "hand:again-lower",
    "probe-plant-report": "worker",
    "probe-crash-worker": "worker",
    "probe-malformed": "worker",
    "probe-shrink-set": "nonce",
}


def failures():
    """The verifier's own report of what failed, by test id.

    The CTRF file drops the parametrised case name, so the case ids come from pytest's summary
    and the CTRF file is what says a run produced a report at all.
    """
    try:
        rows = json.loads(CTRF.read_text(encoding="utf-8"))["results"]["tests"]
    except Exception:
        return None
    names = [row["name"] for row in rows if row.get("status") != "passed"]
    try:
        text = pathlib.Path("/tmp/ccl-last-verifier.txt").read_text(encoding="utf-8")
    except OSError:
        text = ""
    ids = re.findall(r"(test_\w+(?:\[[^\]]+\])?)", text)
    return names + [one for one in ids if "[" in one]


def caught_by(names, out):
    """Which layer of the verifier turned this submission down, from its own report."""
    if names is None:
        return "no report"
    found = []
    # A record that never arrived, or arrived in the wrong shape, is the first thing to say:
    # it fails every case at once, so the case ids underneath it mean nothing.
    for mark in ("stage one left no readable record", "the record is not an object",
                 "the record has no ran and broke tables", "no record for ",
                 "was not the one that ran", "is not a list of lines"):
        if mark in out:
            found.append("worker")
            break
    picked = sorted({one.split("[")[1].rstrip("]") for one in names if "[" in one})
    if picked and "worker" not in found:
        found.append("hand:" + ",".join(picked))
    elif not picked and any("enumerated_program" in one for one in names):
        found.append("hand:unnamed")
    if "test_generated_program" in out:
        found.append("nonce")
    if "test_every_family_was_run" in out:
        found.append("population")
    if "test_the_twin_still_makes_the_frozen_answers" in out:
        found.append("sealed twin")
    return "|".join(found) if found else "nothing failed"


def holds(want, got):
    """Every layer the cheat was built for shows up, and `no-hand` means no case failed."""
    for part in want.split("+"):
        if part == "no-hand":
            if "hand:" in got:
                return False
        elif part.startswith("hand:"):
            if part[5:] not in got:
                return False
        elif part not in got:
            return False
    return True


def main():
    rows = []
    for cheat in sorted((TASK / "cheat").glob("*.sh")):
        name = cheat.stem[len("cheat-"):]
        done = subprocess.run([sys.executable, str(HERE / "host_trial.py"), "--cheat", str(cheat)],
                              capture_output=True, text=True, timeout=3600)
        reward = 1 if "reward=1" in done.stdout else 0
        timed = "worker exit 124" in done.stdout or "worker exit 137" in done.stdout
        names = failures()
        report = pathlib.Path("/tmp/ccl-last-verifier.txt")
        text = report.read_text(encoding="utf-8") if report.is_file() else done.stdout
        got = "clock" if timed else caught_by(names, text)
        want = WANT.get(name, "?")
        ok = reward == 0 and (want == "?" or holds(want, got))
        rows.append((name, reward, got, want, ok))
        print("%-26s reward=%d caught by %-34s want %-18s %s"
              % (name, reward, got[:34], want, "ok" if ok else "MISMATCH"), flush=True)
    bad = [r for r in rows if not r[4]]
    print("%d cheats, %d scored 0, %d caught by the layer they were built for"
          % (len(rows), sum(1 for r in rows if r[1] == 0), len(rows) - len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
