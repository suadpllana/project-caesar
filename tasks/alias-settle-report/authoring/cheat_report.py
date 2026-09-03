"""Which test catches each cheat, through the real two-image trial.

A sweep that only reads the reward cannot tell a probe that was rejected from a
probe that never ran. Both look like 0. So this records the test that fired, per
cheat, and holds each family to what it is aimed at:

  mistake-*  must be caught by a test that reads the rows. A mistake caught only
             by an attestation is a mistake that never reached the machine.

  reward-*   must be caught by something, and must not have moved the reward.
             These are built on the shipped tree, so they are wrong on the rows
             as well; what matters is that the reward channel did not move.

  attest-*   must be caught by the attestation they are aimed at. These are the
             reference with every answer correct, so if the layer does not fire
             nothing else will, and a probe that comes back 1 says the layer is
             decoration.
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(TASK))
SLUG = os.path.basename(TASK)

ROWS = ("test_the_run_left_a_readable_report",
        "test_the_row_a_filing_carries", "test_filings_land_in_the_stated_order",
        "test_what_an_open_tag_can_still_weld", "test_what_a_difference_rules_out",
        "test_what_a_run_can_still_post", "test_the_sets_that_ship_in_the_tree",
        "test_the_sets_made_after_the_agent_stopped",
        "test_the_filing_table_agrees_with_the_rows")

WANT = {
    "cheat-attest-swap-the-emitter": ("test_the_run_finished_every_set",
                                "test_the_sealed_machine_ran_as_shipped"),
    "cheat-attest-swap-a-sealed-function": ("test_the_sealed_machine_ran_as_shipped",),
    "cheat-attest-disarm-the-counter": ("test_the_rows_came_through_the_emitter",),
}


def main():
    box = os.path.join(TASK, "cheat")
    names = sorted(n for n in os.listdir(box) if n.endswith(".sh"))
    bad = 0
    for name in names:
        hits, reward = detail(os.path.join(box, name))
        stem = name[:-3]
        note = "reward %d  caught by: %s" % (reward, ", ".join(hits) or "NOTHING")
        ok = reward == 0 and hits
        if stem.startswith("cheat-mistake-") and not any(h in ROWS for h in hits):
            ok = False
            note += "   [no row test fired - did the cheat reach the machine?]"
        for key, need in WANT.items():
            if stem == key and not any(h in need for h in hits):
                ok = False
                note += "   [not caught by its own attestation]"
        bad += not ok
        print("%-40s %s" % (stem, note))
    print("%d of %d cheats behaved as required" % (len(names) - bad, len(names)))
    return 1 if bad else 0


def detail(script):
    """Re-run inside the verifier image and read the failing test names."""
    import tempfile
    from pathlib import Path
    sys.path.insert(0, os.path.join(REPO, "tools"))
    import docker_trial2 as dt
    t = dt.Trial(SLUG)
    tmp = Path(tempfile.mkdtemp())
    try:
        t.agent_run(Path(script), tmp / "art", False)
        parents = " ".join(sorted({str(Path("/app") / a).rsplit("/", 1)[0]
                                   for a in t.arts}))
        cmd = ("mkdir -p %s ; cp -a /artifacts/. /app/ 2>/dev/null ; "
               "mkdir -p /logs/verifier ; bash /tests/test.sh > /tmp/v.log 2>&1 ; "
               "echo REWARD=$(cat /logs/verifier/reward.txt 2>/dev/null) ; "
               "grep -oE '^FAILED [^ ]+' /tmp/v.log | sed 's#.*::##' | "
               "sed 's#\\[.*##' | sort -u ; "
               "grep -q 'left no readable report' /tmp/v.log "
               "&& echo test_the_run_left_a_readable_report || true" % parents)
        proc = dt.sh(["docker", "run", "--rm",
                      "-v", "%s:/artifacts:ro" % (tmp / "art").resolve(),
                      t.test_img, "bash", "-c", cmd])
        got = proc.stdout.split()
        reward = 1 if "REWARD=1" in got else 0
        return sorted(set(x for x in got if x.startswith("test_"))), reward
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
