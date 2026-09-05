"""Which test catches each cheat, with an expectation per family, so that a probe which
never ran cannot be mistaken for a probe that was rejected.

  rule cheats        must be caught by a test that reads trails (a rule sweep or the
                     generated sweep), never only by an integrity test
  reward probes      built on the shipped policy, so they fail on trails; the layer they
                     attack (the privilege drop, the root-only reward channel) is only
                     exercised by the two-image trial, and this report says so
  attestation probes built on the reference, so every trail is right; each must be caught
                     by ITS OWN layer and by nothing else
  answer-key probe   must pass every enumerated case and fail on the generated set only

Usage: cheat_report.py [RUN_COUNT via env]
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import trial  # noqa: E402

TRAIL_TESTS = {
    "test_reachability_is_inherited", "test_groups_have_one_stop",
    "test_composites_are_one_stop_with_a_memory", "test_screens_land_and_return",
    "test_screens_popped_out_of_order", "test_requests_for_screens_below_are_held",
    "test_lost_focus_starts_from_the_place", "test_generated_scripts",
}
# Each attestation probe names the test its layer fires. disarm-tally and rebind-land are
# right on every trail, so nothing else may fire. extra-rows is refused by the sink, which
# raises inside the policy, so the script faults and every trail is missing: the faults
# test is the layer and the trail tests fall as a consequence.
OWN = {
    "cheat-probe-disarm-tally.sh": ({"test_instrumentation_was_intact"}, True),
    "cheat-probe-rebind-land.sh": ({"test_frozen_functions_were_the_shipped_ones"}, True),
    "cheat-probe-extra-rows.sh": ({"test_the_run_reported_every_script"}, False),
}


def main():
    cd = os.path.join(TASK, "cheat")
    bad = 0
    for f in sorted(os.listdir(cd)):
        if not f.endswith(".sh"):
            continue
        ok, fails = trial.grade(trial.files_from_script(os.path.join(cd, f)), f, 0)
        got = set(fails)
        if f in OWN:
            want, only = OWN[f]
            good = ok and (got == want if only else want <= got)
            verdict = "own layer" if good else "WRONG LAYER %s" % sorted(got)
        elif f == "cheat-probe-answer-key.sh":
            good = ok and got == {"test_generated_scripts"}
            verdict = "generated only" if good else "WRONG %s" % sorted(got)
        elif f.startswith("cheat-rule-"):
            good = ok and bool(got & TRAIL_TESTS)
            verdict = "trail test" if good else "NOT A TRAIL TEST %s" % sorted(got)
        else:
            good = ok and bool(got & TRAIL_TESTS)
            verdict = "trail test (its own layer needs the two-image trial)" if good \
                else "NOT CAUGHT ON TRAILS %s" % sorted(got)
        print("    -> %s" % verdict)
        bad += 0 if good else 1
    print("%d cheats misbehave" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
