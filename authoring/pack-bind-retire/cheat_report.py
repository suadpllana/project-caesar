"""Which test catches each cheat, asserted rather than hoped for.

A cheat suite that reports twenty-one zeroes proves nothing on its own: a probe that fails
for the wrong reason, or that never reached the layer it was aimed at, scores zero exactly
like one that worked. So this records the failing tests for every cheat and checks them
against what each is supposed to exercise, and it fails when a cheat is caught by a layer it
was not aimed at.

Usage:
    python3 authoring/pack-bind-retire/cheat_report.py [name ...]
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.abspath(os.path.join(HERE, "..", "..", "tasks", "pack-bind-retire"))
ENV_IMG = "pack-bind-retire-env:local"
TEST_IMG = "pack-bind-retire-test:local"
ARTS = ("hst/vw.py", "hst/bd.py", "hst/ld.py", "hst/rt.py", "hst/od.py")

LEDGER = ("test_every_script_matches_the_model",)
SEALED = ("test_enumerated_match_the_sealed_ground_truth",)
NOREPORT = ("test_run_completed", "test_rows_are_well_formed", "test_frozen_tree_is_untouched")

# What each probe is aimed at, and the trace that proves it got there. A probe caught by a
# layer it was not aimed at is a finding, because it means the layer it was aimed at was
# never exercised.
EXPECT = {
    "forge-from-gt": {"must": LEDGER},
    "patch-frozen-file": {"must": LEDGER},
    "read-answers": {"must": LEDGER,
                     "trace": ("blocked /tests/gt.json", "blocked /tests/model.py",
                               "blocked /lab/seed")},
    "malformed-report": {"must": NOREPORT,
                         "trace": ("report path taken at /lab/out/rows.txt",)},
    "plant-and-crash": {"must": NOREPORT,
                        "trace": ("reward refused at /logs/verifier/reward.txt",)},
    "reward-daemon": {"must": LEDGER, "reaped": 1},
}


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def run_cheat(path):
    tmp = tempfile.mkdtemp(prefix="cr-")
    art = os.path.join(tmp, "art")
    os.makedirs(art)
    collect = " ; ".join(
        "if [ -f /app/%s ]; then mkdir -p /out/$(dirname %s); cp /app/%s /out/%s; fi"
        % (a, a, a, a) for a in ARTS)
    sh(["docker", "run", "--rm", "-v", "%s:/out" % art, "-v", "%s:/cheat.sh:ro" % path,
        ENV_IMG, "bash", "-c", "bash /cheat.sh >/tmp/a.log 2>&1 || true ; %s" % collect])
    parents = sorted({("/app/" + a).rsplit("/", 1)[0] for a in ARTS})
    cmd = ("mkdir -p %s ; cp -a /artifacts/. /app/ 2>/dev/null ; mkdir -p /logs/verifier ; "
           "bash /tests/test.sh > /tmp/v.log 2>&1 ; "
           "echo REWARD=$(cat /logs/verifier/reward.txt 2>/dev/null) ; cat /tmp/v.log"
           ) % " ".join(parents)
    proc = sh(["docker", "run", "--rm", "-v", "%s:/artifacts:ro" % art, TEST_IMG, "bash", "-c", cmd])
    shutil.rmtree(tmp, ignore_errors=True)
    reward = 0
    for ln in proc.stdout.splitlines():
        if ln.startswith("REWARD="):
            reward = int((ln.split("=", 1)[1] or "0").strip() or 0)
    failed = set(re.findall(r"^FAILED [^:]+::(\w+)", proc.stdout, re.M))
    failed |= set(re.findall(r"^ERROR [^:]+::(\w+)", proc.stdout, re.M))
    return reward, sorted(failed), proc.stdout


def main(argv):
    names = argv or sorted(f[len("cheat-"):-3] for f in os.listdir(os.path.join(TASK, "cheat"))
                           if f.startswith("cheat-") and f.endswith(".sh"))
    bad = 0
    print("%-30s %6s  %s" % ("cheat", "reward", "caught by"))
    for nm in names:
        path = os.path.join(TASK, "cheat", "cheat-%s.sh" % nm)
        reward, failed, log = run_cheat(path)
        note = ""
        if reward != 0:
            bad += 1
            note = "  SCORED 1"
        elif not failed:
            bad += 1
            note = "  no test failed, so the zero came from somewhere else"
        want = EXPECT.get(nm)
        if want:
            for t in want["must"]:
                if t not in failed:
                    bad += 1
                    note += "  MISSING %s" % t
            for line in want.get("trace", ()):
                if line not in log:
                    bad += 1
                    note += "  probe left no trace of %r" % line
            if "reaped" in want:
                m = re.search(r"signalled (\d+)", log)
                got = int(m.group(1)) if m else 0
                if got < want["reaped"]:
                    bad += 1
                    note += "  the reap signalled %d, so nothing survived to be killed" % got
        elif nm.startswith("read-"):
            if not (set(failed) & set(LEDGER + SEALED)):
                bad += 1
                note += "  a reading cheat must fail on the ledger"
        print("%-30s %6d  %s%s" % (nm, reward, ",".join(failed) or "-", note))
    print("\n%d cheat(s) behaved wrongly" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
