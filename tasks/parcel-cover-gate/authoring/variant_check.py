"""Every alternative correct implementation has to score 1 through the real grader.

This is the mirror of the cheat suite and it is the gate the run audit actually
applies. A verifier that grades the way the reference happens to be written
rather than the behaviour the requirements describe fails a correct submission,
and that reads to an auditor exactly like a task built to be gamed.

A variant scoring anything but 1 is a finding about the brief before it is a
finding about the variant. Ask which sentence separates it from the reference. If
the honest answer is "none", the rule was never decided and the variant has just
found that for free - which is what happened twice here on 2026-09-03, and both
of those moved to `cheat/` with a named feed pinning them.
"""

import sys

import lab
import trial


def main(argv):
    count = int(argv[argv.index("--count") + 1]) if "--count" in argv else 120
    nonce = "variant-check"
    bad = 0
    got, note = trial.grade(lab.reference(), nonce, count)
    print("%s  %-24s reward %d  %s"
          % ("ok " if got == 1 else "BAD", "reference", got, note[:70]))
    bad += 0 if got == 1 else 1
    for d in sorted(p for p in (lab.ROOT / "authoring" / "variants").iterdir()
                    if p.is_dir()):
        over = dict(lab.reference())
        for f in sorted(d.glob("*.py")):
            over[f.name] = f.read_text()
        got, note = trial.grade(over, nonce, count)
        print("%s  %-24s reward %d  %s"
              % ("ok " if got == 1 else "BAD", d.name, got, note[:70]))
        bad += 0 if got == 1 else 1
    print("\n%s" % ("every correct reading scores 1" if not bad
                    else "%d correct readings do not score 1" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
