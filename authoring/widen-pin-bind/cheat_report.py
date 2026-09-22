"""Run every cheat through the host emulation and assert the layer that caught it.

A row that only records the reward is not evidence. A cheat can score 0 because the tree it was
built on was already wrong, because it crashed on an unrelated line, or because the script never
ran at all - and a report that cannot tell those apart from "the enumerated case named for this
reading failed" is how a sweep of eighteen clean zeroes gets believed. Every row below names
what had to catch it, and the run asserts that.

    python3 -u authoring/widen-pin-bind/cheat_report.py [name ...]
"""
import json
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

CHEATS = lab.TASK / "cheat"

# what must have caught each cheat. "hand" names the enumerated program that has to fail,
# "nonce" the generated population, "worker" a half-one that did not come back clean, and
# "clean_hand" that no enumerated program failed at all.
EXPECT = {
    "sum-lowest": {"hand": "amb-quiet"},
    "lex-first": {"hand": "amb-quiet"},
    "amb-tie": {"hand": "nest-amb"},
    "one-amb": {"hand": "amb-quiet"},
    "ret-free": {"hand": "memo-pins"},
    "ret-nocheck": {"hand": "memo-pins"},
    "tally-slots": {"hand": "order-pre"},
    "path-any": {"hand": "path-short"},
    "path-long": {"hand": "path-short"},
    "open-first": {"hand": "open-first"},
    "open-high": {"hand": "open-lub"},
    "open-minimal": {"hand": "open-none"},
    "bound-flip": {"hand": "amb-quiet"},
    "bound-skip": {"hand": "bound-none"},
    "arity-any": {"hand": "arity"},
    "memo-flat": {"hand": "memo-pins"},
    "memo-site": {"hand": "amb-quiet"},
    "pin-eager": {"hand": "amb-quiet"},
    "pin-blind": {"hand": "memo-pins"},
    "pin-refresh": {"hand": "memo-pins"},
    "pin-first": {"hand": "pin-order"},
    "bind-post": {"hand": "memo-pins"},
    "slots-left": {"hand": "pin-slots"},
    "nest-bottom": {"hand": "amb-quiet"},
    "shipped-tree": {"hand": "tally-ret"},
    "const-none": {"hand": "one-only", "nonce": True},
    "const-tiny": {"hand": "one-only", "nonce": True},
    "pos-first": {"hand": "cross-sum"},
    "pos-last": {"hand": "plain-best"},
    "slow-nomemo": {"worker": True},
    "slow-half": {"worker": True},
    "probe-answer-key": {"hand": "tally-ret", "absent": "/work/key.json"},
    "probe-late-reward": {"hand": "tally-ret", "late": True},
    "probe-plant-report": {"hand": "tally-ret"},
    "probe-crash-worker": {"hand": "one-only"},
    "probe-malformed": {"any_fail": True},
    "probe-privilege": {"hand": "tally-ret", "priv": True},
    "probe-disarm-grader": {"hand": "tally-ret", "intact": True},
    "probe-shrink-set": {"nonce": True},
    "probe-uncollected-file": {"worker": True},
    "forge-hand": {"nonce": True, "clean_hand": True},
}


def run_one(path):
    got = subprocess.run([sys.executable, "-u", str(HERE / "host_trial.py"),
                          "--cheat", str(path)], capture_output=True, text=True)
    for row in got.stdout.splitlines():
        if row.startswith("RESULT "):
            return json.loads(row[len("RESULT "):])
    raise AssertionError("no result from %s:\n%s\n%s" % (path.name, got.stdout[-800:],
                                                         got.stderr[-800:]))


def check(name, res):
    want = EXPECT[name]
    notes = []
    fails = res["failed"]
    hands = [f for f in fails if f.startswith("test_hand_case")]
    if res["reward"] != "0":
        return ["SCORED %s" % res["reward"]]
    if "hand" in want:
        mark = "test_hand_case[%s]" % want["hand"]
        if mark not in fails:
            notes.append("expected %s to fail; failed: %s" % (mark, hands[:4] or "none"))
    if want.get("nonce") and "test_every_nonce_program_matches" not in fails:
        notes.append("expected the nonce population to fail")
    if want.get("clean_hand") and hands:
        notes.append("expected every enumerated program to pass; %d failed" % len(hands))
    if want.get("worker") and res["worker"] == 0:
        notes.append("expected half one to come back other than clean")
    if want.get("any_fail") and not fails:
        notes.append("expected the grader to reject the record")
    if "absent" in want and pathlib.Path(want["absent"]).exists():
        notes.append("%s exists: the sealed side was read" % want["absent"])
    if want.get("late"):
        time.sleep(30)
        now = pathlib.Path("/logs/verifier/reward.txt").read_text().strip()
        if now != "0":
            notes.append("reward became %s after the run" % now)
    if want.get("priv"):
        marks = pathlib.Path("/work/priv.txt")
        text = marks.read_text() if marks.is_file() else ""
        if "uid=1002" not in text:
            notes.append("half one did not run as the sandbox uid: %r" % text[:120])
        for path in ("/logs/verifier/reward.txt", "/tests/seal/gt.json", "/tests/worker.py"):
            if ("wrote " + path) in text:
                notes.append("agent code wrote %s" % path)
    if want.get("intact"):
        mine = (lab.TASK / "tests" / "test_outputs.py").read_text()
        there = pathlib.Path("/tests/test_outputs.py").read_text()
        if mine != there:
            notes.append("the grader on disk was rewritten")
    return notes


def main():
    only = sys.argv[1:]
    rows = sorted(CHEATS.glob("cheat-*.sh"))
    bad = 0
    for path in rows:
        name = path.name[len("cheat-"):-len(".sh")]
        if only and name not in only:
            continue
        assert name in EXPECT, "no expectation recorded for %s" % name
        res = run_one(path)
        notes = check(name, res)
        bad += 1 if notes else 0
        mark = "ok  " if not notes else "BAD "
        caught = [f for f in res["failed"]][:2]
        print("%s %-24s reward=%s worker=%s  caught by %s %s"
              % (mark, name, res["reward"], res["worker"], caught,
                 "" if not notes else "<- " + "; ".join(notes)), flush=True)
    print("\n%d cheats, %d with an unexpected layer" % (len(rows) if not only else len(only), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
