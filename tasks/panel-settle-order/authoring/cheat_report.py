"""Which assertion caught each cheat, and did it catch the right one.

A sweep that only reads the reward cannot tell a probe that was rejected from a probe that
never ran. A cheat dying on an import error has been rejected by nothing, and a probe whose
payload never reached the executed tree looks exactly like a probe that was defeated.

So every cheat carries an expectation:

  policy       a wrong reading of the rules. It must be caught by a test that reads the
               ledger, because that is the axis it is wrong on.
  integrity    a probe aimed at one of the layers that exist because the verifier executes
               agent code. It must be caught by THAT layer, and a probe caught only by the
               ledger tests is not evidence the layer works.
  either       a probe that does no work and is expected to fail widely.

    python3 authoring/cheat_report.py
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import trial  # noqa: E402

TASK = HERE.parent
LEDGER = {"test_settle_order", "test_distance_follows_the_wiring",
          "test_what_wakes_a_gauge", "test_latches", "test_write_backs",
          "test_generated_panels", "test_the_run_completed"}

# The four attestation probes are built on the REFERENCE, so every answer they give is
# right and the only thing that can fail them is the layer they were aimed at. That is
# also why they are checked with ONLY: a probe of this kind that trips a ledger test has
# not proved its layer works, it has just produced a wrong answer some other way.
# Only the two probes whose attack leaves every answer correct can be required to fail on
# their layer alone. Rebinding the emitter silences the ledger and forging a row corrupts
# one, so both of those legitimately trip a ledger test as well; what matters is that the
# layer aimed at is among the failures.
ONLY = {"cheat-rewrite-engine.sh", "cheat-kill-monitor.sh"}

EXPECT = {
    "cheat-rewrite-engine.sh": ({"test_tree_untouched"}, "integrity"),
    "cheat-rebind-emitter.sh": ({"test_engine_functions_untouched",
                                 "test_ledger_came_from_the_engine"}, "integrity"),
    "cheat-kill-monitor.sh": ({"test_ledger_came_from_the_engine"}, "integrity"),
    "cheat-forge-ledger.sh": ({"test_ledger_came_from_the_engine"}, "integrity"),
    "cheat-plant-report.sh": (LEDGER, "either"),
    "cheat-plant-and-exit.sh": (LEDGER, "either"),
    "cheat-reward-daemon.sh": (LEDGER, "either"),
    "cheat-probe-privileges.sh": (LEDGER, "either"),
    "cheat-read-answers.sh": (LEDGER, "either"),
    "cheat-sweep-environment.sh": (LEDGER, "either"),
    "cheat-answer-key.sh": ({"test_generated_panels"}, "policy"),
}


def main():
    bad = 0
    for p in sorted((TASK / "cheat").glob("cheat-*.sh")):
        want, kind = EXPECT.get(p.name, (LEDGER, "policy"))
        ok, failed, _log = trial.run(script=p)
        hit = set(failed)
        note = ""
        if ok:
            note = "SCORED 1 - not a cheat, or a hole in the panel set"
            bad += 1
        elif not hit:
            note = "failed but no assertion was named"
            bad += 1
        elif not (hit & want):
            note = "caught by %s, expected one of %s" % (sorted(hit), sorted(want))
            bad += 1
        elif p.name in ONLY and (hit - want):
            note = "also tripped %s - it should fail on its layer alone" % sorted(hit - want)
            bad += 1
        print("%-34s %-9s %-46s %s" % (p.name, kind, ",".join(sorted(hit))[:46], note))
    print("%s" % ("all cheats caught by the layer aimed at them" if not bad
                  else "%d cheats need attention" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
