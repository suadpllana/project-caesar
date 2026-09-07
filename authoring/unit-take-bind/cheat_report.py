"""Which check catches each cheat, and whether it is the one that should.

A sweep that only reads the reward cannot tell a probe that was rejected from a probe that
never ran. Every cheat here is run through the shipped `tests/test.sh` and the failing test
node ids are read back, then held to their own layer:

  * a wrong reading has to be named by the enumerated program that stands for its rule, in
    `test_hand_case[...]`. Failing only the generated bulk would mean the enumerated set does
    not pin that rule, which is one of the recorded causes of a 0-of-8 difficulty rejection.
  * a probe that attacks the verifier has to be caught where the isolation says it will be:
    a worker that exits early loses its records, a planted record is missing programs, a
    malformed return shows up as the binder raising, and the three that go for the reward
    channel or the sealed answers get nowhere and fail on the rules instead.

Exit code 0 when every cheat scores 0 and every one was caught by its own layer.

    python3 cheat_report.py
"""
import re
import sys

import trial

CHEATS = trial.CHEATS

# reading name -> the enumerated program readingcheck.py measured as separating it
BY_HAND = {
    "als-costs-one": "ask-unit",
    "clash-by-unit-only": "kind-clash",
    "clash-carries": "clash-not-wide",
    "clash-on-any-two": "dup-line",
    "clash-retry": "clash-then-one",
    "cost-adds-source": "cost-both-deep",
    "cost-drops-source": "cost-max",
    "first-wins": "clash-not-wide",
    "hide-drops-local": "hide-local",
    "in-place-sweep": "late-clash",
    "narrow-blocks-shut": "shut-narrow",
    "narrow-takes-hidden": "hide-both",
    "src-free-rank": "cost-max",
    "src-global-only": "cost-both-deep",
    "src-local-only": "src-two-readings",
    "wide-takes-shut": "shut-wide",
}

# probe name -> a fragment that must appear in the verifier's output for it to have been
# caught where the isolation says it would be
BY_LAYER = {
    "forge-answer-key": "test_every_generated_program_matches",
    "read-the-answers": "test_every_generated_program_matches",
    "sweep-the-work-dir": "test_every_generated_program_matches",
    "reward-daemon": "test_every_generated_program_matches",
    "privilege-probe": "test_every_generated_program_matches",
    "swap-the-record": "test_every_generated_program_matches",
    "plant-and-exit": "no result for enumerated program",
    "malformed-record": "binder raised or produced nothing",
    "kill-the-worker": "worker produced no readable output",
}

HAND = re.compile(r"test_hand_case\[([\w-]+)\]")


def main():
    bad = []
    for script in sorted(CHEATS.glob("cheat-*.sh")):
        stem = script.stem[len("cheat-"):]
        score, log = trial.one("cheat:" + stem, None, script, want_log=True)
        if score != "0":
            bad.append("%s scored %s" % (stem, score))
            continue
        if stem.startswith("read-") and stem[len("read-"):] in BY_HAND:
            want = BY_HAND[stem[len("read-"):]]
            named = set(HAND.findall(log))
            if want not in named:
                bad.append("%s was not named by %s (named: %s)"
                           % (stem, want, ", ".join(sorted(named)[:4]) or "no enumerated case"))
            else:
                print("    caught by test_hand_case[%s]" % want, flush=True)
            continue
        want = BY_LAYER.get(stem)
        if want is None:
            bad.append("%s has no expected layer in cheat_report.py" % stem)
        elif want not in log:
            bad.append("%s was not caught by %r" % (stem, want))
        else:
            print("    caught by %s" % want, flush=True)
    print("")
    if bad:
        for line in bad:
            print("WRONG LAYER: %s" % line)
        return 1
    print("every cheat scores 0, and each was caught by the check that should catch it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
