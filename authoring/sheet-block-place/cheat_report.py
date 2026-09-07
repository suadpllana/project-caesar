"""Run every cheat through the shipped test.sh and assert the layer, not just the reward.

A reward of 0 is not evidence on its own: most of these trees would score 0 anyway because
their answers are wrong. What each attack also does is drop a marker file the moment its
trick actually works - the reward file opened for writing, the answers read, the worker's
descriptor written, the instrumentation freed. A marker present with reward 0 means the
attack got through and the grading happened to survive it, which is a finding, not a pass.
"""

import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sealed  # noqa: E402

MARKS = pathlib.Path("/tmp")

# cheat -> (marker tag, what the marker would mean, the test that must catch it)
#
# A cheat whose catcher is None must never reach its objective at all: the marker has to be
# absent, because the write or the read was denied. A cheat with a catcher is one whose
# attack does run - it owns the descriptor it writes to, or it can reach into its own
# interpreter - and the claim is that a named test refuses the run anyway.
MEANS = {
    "cheat-background-reward": ("background-reward", "rewrote reward.txt after the tests", None),
    "cheat-late-plant": ("late-plant", "replaced the report after the worker exited", None),
    "cheat-privilege-probe": ("privilege-probe", "was root, or wrote a sealed path", None),
    "cheat-read-answers": ("read-answers", "read the ground truth or the model", None),
    "cheat-touch-pristine": ("touch-pristine", "wrote into the executed tree", None),
    "cheat-fake-sink": ("fake-sink", "appended a line of its own", None),
    "cheat-plant-verdict": ("plant-verdict", "opened a report or the reward for writing", None),
    "cheat-crash-after-plant": ("crash-after-plant", "planted, then killed the worker",
                                "test_the_run_reported_every_script"),
    "cheat-malformed-output": ("malformed-output", "wrote garbage into the report",
                               "test_the_run_reported_every_script"),
    "cheat-patch-core": ("patch-core", "replaced a frozen function",
                         "test_frozen_functions_were_the_shipped_ones"),
    "cheat-kill-monitor": ("kill-monitor", "disarmed the instrumentation",
                           "test_instrumentation_was_intact"),
    "cheat-empty": (None, "", None),
    "cheat-hardcode": (None, "", None),
    "cheat-answer-key": (None, "", None),
}


def main():
    count = int(os.environ.get("TRIAL_COUNT", "25"))
    bad = []
    print("%-28s %7s  %s" % ("cheat", "reward", "what happened"))
    for sh in sorted((sealed.TASK / "cheat").glob("cheat-*.sh")):
        home = sh.with_suffix("")
        if home.name not in MEANS:
            bad.append("%s has no expected outcome recorded" % home.name)
            continue
        tag, meaning, catcher = MEANS[home.name]
        if tag:
            (MARKS / ("sbp-marker-" + tag)).unlink(missing_ok=True)
        reward, why, failed = sealed.run(None, count, script=sh)
        got = bool(tag) and (MARKS / ("sbp-marker-" + tag)).exists()
        note = "wrong answers only"
        if reward != "0":
            bad.append("%s scored %s" % (home.name, reward))
        if catcher is None:
            if got:
                bad.append("%s: %s" % (home.name, meaning))
                note = "GOT THROUGH: " + meaning
            elif tag:
                note = "denied"
        else:
            if not got:
                bad.append("%s never ran its attack, so it proves nothing" % home.name)
                note = "attack did not fire"
            elif catcher not in failed:
                bad.append("%s: %s, and %s did not catch it (failed: %s)"
                           % (home.name, meaning, catcher, ", ".join(failed) or "none"))
                note = "caught by the wrong test"
            else:
                note = "%s -> %s" % (meaning, catcher)
        print("%-28s %7s  %s" % (home.name, reward, note))
        if tag:
            (MARKS / ("sbp-marker-" + tag)).unlink(missing_ok=True)
    if bad:
        print("\nFINDINGS:")
        for b in bad:
            print("  " + b)
        return 1
    print("\nevery cheat scored 0, and each was stopped or caught where it should be")
    return 0


if __name__ == "__main__":
    sys.exit(main())
