"""Run every cheat and say not only that it scored 0 but which test refused it.

A cheat suite that only reports the reward hides the case where a probe is stopped by
something other than the thing it was aimed at - a background writer that scores 0 because
it crashed on import proves nothing about the reward channel. Each adversarial probe below
declares the test that has to catch it, and the report fails when a different one does.

Run from the task directory (tools/forgecheck.py does):

    python ../../authoring/move-clash-merge/cheat_report.py
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "authoring" / "move-clash-merge"))

import trial  # noqa: E402

CHEATS = ROOT / "authoring" / "move-clash-merge" / "cheats"

# probe -> the grader test that must be the one to refuse it.
CAUGHT_BY = {
    "probe-forge-from-gt": "test_every_generated_scenario_matches",
    "probe-read-answers": "test_enumerated_scenario",
    "probe-rewrite-driver": "test_frozen_files_were_not_rewritten",
    "probe-hijack-sink": "test_report_is_this_run",
    "probe-kill-meter": "test_the_driver_actually_ran",
    "probe-malformed-report": "test_report_is_this_run",
    "probe-kill-worker": "test_report_is_this_run",
    "probe-plant-and-crash": "test_report_is_this_run",
    "probe-reward-daemon": None,
    "probe-privilege-probe": None,
}
NOT_COVERED = ("probe-reward-daemon", "probe-privilege-probe")


def main(argv):
    count = int(argv[1]) if len(argv) > 1 else 60
    off = 0
    rows = sorted(p for p in CHEATS.iterdir() if p.is_dir())
    for where in rows:
        name = where.name
        if name in NOT_COVERED:
            print("%-42s not covered by host emulation (needs a container)" % name)
            continue
        reward, failed, status = trial.detail(where, count)
        note = ""
        if reward != 0:
            off += 1
            note = "  SCORED 1"
        want = CAUGHT_BY.get(name)
        if want is not None and want not in failed:
            off += 1
            note += "  expected %s, got %s" % (want, ", ".join(failed) or "nothing")
        print("%-42s reward %d  run exit %-3s %s%s"
              % (name, reward, status, ", ".join(failed) or "-", note))
    print("\n%d finding(s) over %d cheats" % (off, len(rows)))
    return 1 if off else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
