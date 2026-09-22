#!/usr/bin/env python3
"""The enumerated plans, derived by hand from the rules before the model was run on them.

This is independent evidence for the sealed model: each plan below was worked out on paper from
the rules as the brief states them - which partitions exist, what the correction reaches, how each
read resolves, the flags, the line and its order - and only then compared with what the model
prints. A disagreement is a bug in one of the two, found before gt.json is frozen. Never ships.

    python3 -u authoring/restate-hold-plan/hand.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402


def temps(name, lo, hi):
    return ["temp %s %d" % (name, h) for h in range(lo, hi + 1)]


def runs(name, lo, hi, word="full"):
    return ["run %s %d %s" % (name, h, word) for h in range(lo, hi + 1)]


HAND = {
    "plain-rerun": ["run cl 30 full", "run tot 1 full", "run wk 1 full", "run wk 2 full"],
    "keep-edge": ["temp cl 88", "temp cl 89", "run cl 90 full", "run sm 90 full",
                  "run sm 91 full", "run sm 92 full"],
    "keep-published": ["temp dy 6", "temp dy 7", "run dy 8 full", "run wk 8 full",
                       "run wk 9 full"],
    "reach-bounded-by-now": runs("hr", 97, 99),
    "reach-through-expired": temps("cl", 96, 119) + ["run tot 4 full", "run wk 4 full",
                                                     "run wk 5 full"],
    "pinned-hold": ["hold dy 6 pinned", "hold wk 6 same"],
    "pinned-part": ["run ev 6 full", "run wk 6 part", "hold dy 6 pinned"],
    "pinned-window-same": ["hold dy 5 pinned", "hold wk 5 same", "hold wk 6 same",
                           "hold wk 7 same"],
    "pinned-unreached": ["run dy 8 full", "run wk 8 full", "run wk 9 full"],
    "same-disagrees": ["run ev 6 full", "run wk 6 part", "hold dy 6 pinned", "hold mid 6 same"],
    "temp-window": ["temp dy 6", "run dy 8 full", "run wk 8 full", "run wk 9 full"],
    "temp-once": ["temp dy 5", "temp dy 6", "run dy 8 full", "run wk 8 full", "run mo 8 full",
                  "run wk 9 full", "run mo 9 full"],
    "temp-only-for-reruns": ["hold dy 8 pinned", "hold wk 8 same"],
    "lost-temps-unprinted": ["temp dy 7", "run dy 8 full", "run wk 9 full", "hold wk 8 lost"],
    "lost-source": ["run dy 8 full", "run wk 8 full", "run wk 9 full", "run mo 9 full",
                    "hold mo 8 lost"],
    "lost-temp-chain": ["temp dy 6", "temp dy 7", "run dy 8 full", "run wk 9 full",
                        "hold wk 8 lost"],
    "lost-before-same": ["hold dy 8 pinned", "hold wk 8 lost"],
    "stand-use": temps("x", 96, 119) + ["run r 4 full", "run s 4 sub"],
    "stand-any-hour": temps("x", 216, 219) + ["run x 225 full", "run r 9 full", "run s 9 sub"],
    "stand-refused-published": temps("x", 96, 119) + ["run s 4 full", "hold r 4 pinned",
                                                      "hold t 4 same"],
    "stand-refused-part": temps("x", 216, 219) + ["run x 224 full", "run s 9 part",
                                                  "run r 9 part", "hold x 225 pinned"],
    # s keeps 48 hours, so its day 7 ended at 192 and is gone at 240: it is computed for the
    # plan too, through the roll-up that was just rerun (the first hand derivation missed that)
    "stand-in-temp": ["temp s 5", "temp s 6"] + temps("x", 168, 191) + [
        "run r 7 full", "temp s 7", "run w 7 full", "run w 8 full", "run w 9 full"],
    "mode-part-over-sub": temps("x", 96, 119) + ["run r 4 full", "run s 4 part",
                                                 "hold p 4 pinned"],
    "order-after-roll-up": temps("x", 96, 119) + ["run u 4 full", "run r 4 full",
                                                  "run s 4 sub"],
    "holds-last": ["run wk 6 part", "run wk 7 full", "run wk 8 full", "hold dy 6 pinned"],
    "chain-published": ["run bal 4 full", "run bal 5 full", "hold bal 6 pinned",
                        "hold bal 7 same", "hold bal 8 same", "hold bal 9 same"],
    "chain-checkpoint": temps("bal", 3, 6) + runs("bal", 7, 9),
    "chain-to-zero": temps("bal", 0, 4) + runs("bal", 5, 6),
    "prehistory": ["run dy 1 full"] + runs("wk", 1, 4),
    "prev-cross": ["run dy 1 full"] + runs("hr", 48, 71) + ["run dl 2 full"],
}


def main():
    cases, _gen, model = lab.sealed()
    bad = 0
    if sorted(HAND) != sorted(cases.ORDER):
        print("hand derivations and cases differ: %s" % sorted(set(HAND) ^ set(cases.ORDER)))
        bad += 1
    for name in cases.ORDER:
        got = model.expect(cases.prog(name))
        want = HAND.get(name)
        if got != want:
            bad += 1
            print("DIFFERS %s" % name)
            print("   model: %s" % got)
            print("   hand:  %s" % want)
    print("%d of %d enumerated plans agree with the hand derivation"
          % (len(cases.ORDER) - bad, len(cases.ORDER)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
