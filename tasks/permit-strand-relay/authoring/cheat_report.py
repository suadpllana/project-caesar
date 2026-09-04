"""Every cheat through the real verifier, with the test that caught it named.

A reward of 0 says nothing on its own. A probe that died on an ImportError, or
one aimed at a path the overlay never copies, scores 0 having exercised
nothing. So each cheat declares what should catch it, and the attestation
probes - the reference with every answer correct and one layer interfered with
- have to be caught by their own layer and by nothing else, which is the only
evidence that layer fires at all.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import trial

# The layer each attestation probe attacks, and the tests that layer owns.
# Disarming the interpreter's counter takes its floor down with it, so both
# belong to one layer; anything outside the set means the probe was rejected
# for a reason other than the one it was built to exercise.
OWN = {
    "probe-kill-monitor": ("test_the_instrumentation_was_armed",
                           "test_the_frozen_calls_were_actually_made"),
    "probe-rebind-frozen": ("test_the_frozen_machine_was_the_one_we_shipped",),
    "probe-rewrite-frozen": ("test_the_executed_tree_was_the_one_we_shipped",),
    "probe-force-row": ("test_no_row_was_offered_by_the_policy",),
}


def main():
    if not trial.build():
        return 1
    home = os.path.join(trial.ROOT, "cheat")
    names = sorted(leaf for leaf in os.listdir(home)
                   if leaf.startswith("cheat-") and leaf.endswith(".sh"))
    bad = 0
    for leaf in names:
        tag = leaf[len("cheat-"):-3]
        reward, log = trial.once(os.path.join(home, leaf))
        fired = trial.failed(log)
        note = ""
        if reward != 0:
            note = "  <-- SCORED %d" % reward
            bad += 1
        elif tag in OWN:
            want = OWN[tag]
            spare = [f for f in fired if f not in want]
            if want[0] not in fired:
                note = "  <-- NOT caught by " + want[0]
                bad += 1
            elif spare:
                note = "  <-- also caught by " + ", ".join(spare)
                bad += 1
        elif not fired:
            note = "  <-- NOTHING named it"
            bad += 1
        print("%-32s reward=%d  %s%s"
              % (tag, reward, ", ".join(fired) or "(none)", note))
    print("%d cheat(s), %d unexpected" % (len(names), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
