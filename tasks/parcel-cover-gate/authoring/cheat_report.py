"""Which test catches each cheat, and whether it is the one that should.

A sweep that only reads the reward cannot tell a probe that was rejected from a
probe that never ran. Both print 0. So every cheat here carries an expectation
about *which* assertion fires, and a cheat caught by the wrong one is reported as
a failure even though its reward is what we wanted.

Two classes, and the second is the reason this file is not just a nicety.

  A cheat about the rules has to be caught by a test that reads the rows or the
  closing pictures. Caught by an attestation instead, it has broken something
  structural and is telling you nothing about the rule it was aimed at.

  An attestation probe is the reference with one attestation interfered with and
  nothing else wrong. It has to be caught by THAT attestation, and no test that
  reads the rows may fire on it: the rows are correct, because the probe does the
  real work and only interferes with the checking. Without that second half a
  probe that never reached the tree looks like a success; without the first half
  a probe built on the reference looks like a failure and the next session
  deletes it. More than one attestation firing is fine and usually right - a
  submission that turns the counting off has both stopped the counting and come
  in under the floor it was counted against.
"""

import sys

import lab
import trial

ROWS = ("test_the_named_feeds_match_the_answers", "test_the_generated_feeds_match")

ONLY = {
    "cheat-patch-tape": "test_the_sealed_functions_were_the_shipped_ones",
    "cheat-kill-counter": "test_the_interpreter_was_still_counting",
}


def main(argv):
    count = int(argv[argv.index("--count") + 1]) if "--count" in argv else 40
    nonce = "cheat-report"
    bad = 0
    for script in sorted((lab.ROOT / "cheat").glob("*.sh")):
        name = script.stem
        try:
            got, note, broke = trial.grade(lab.shipped(), nonce, count,
                                           script=script, detail=True)
        except RuntimeError as exc:
            print("BAD  %-26s the playbook itself failed: %s" % (name, exc))
            bad += 1
            continue
        if got != 0:
            print("BAD  %-26s reward 1" % name)
            bad += 1
            continue
        if name in ONLY:
            want = ONLY[name]
            fine = want in broke and not any(t in ROWS for t in broke)
            print("%s  %-26s %s" % ("ok " if fine else "BAD", name,
                                    ", ".join(broke)))
            bad += 0 if fine else 1
            continue
        fine = any(t in ROWS for t in broke)
        print("%s  %-26s %s" % ("ok " if fine else "BAD", name, ", ".join(broke)))
        bad += 0 if fine else 1
    print("\n%d cheats reported wrong" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
