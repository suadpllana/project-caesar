"""Which graded axis separates each cheat, and on how many journals.

Two things this is for.

NO GRADED FIELD IS DEAD WEIGHT. An axis that separates no cheat cannot catch a wrong
answer and can still fail a right one, which makes it pure liability. Both axes here -
the answers to the questions, and the holdings digest after every operation - have to
earn their place.

THE LOTTERY CHECK, which is the one that has cost a rejection in this repo before. A cheat
that differs from the reference on a handful of journals out of hundreds is not testing
expertise, it is testing the draw: `cheat-spawn-order` in an earlier task differed on one
program in 427, which under all-or-nothing grading is a coin flip rather than a test of
whether the solver understood anything. Anything in single digits here wants either a
sharper enumerated case or a generator that produces the situation more often.

    python authoring/field_report.py --count 200
"""

import argparse
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(HERE))

import cases  # noqa: E402
import gen  # noqa: E402
import harness  # noqa: E402

BODY = re.compile(r'cat > "\$APP/pol/(\S+?)" <<\'GSO_EOF\'\n(.*?)\nGSO_EOF', re.S)

# These two are the reference with one attestation interfered with. They are behaviourally
# identical to a correct submission on purpose - that is the whole point of them - so this
# report, which measures behaviour only, cannot separate them and must not claim to. They
# are rejected by test_every_row_came_through_the_emitter and by the tree and fingerprint
# checks respectively, which authoring/cheat_report.py is the place to confirm.
BY_ATTESTATION = ("cheat-quiet-monitor", "cheat-swap-kernel")


def policy_of(path, box):
    """Unpack a cheat's four files into a directory the harness can overlay."""
    files = dict(BODY.findall(path.read_text()))
    if not files:
        return None
    box.mkdir(parents=True, exist_ok=True)
    for name, body in files.items():
        (box / name).write_text(body.rstrip("\n") + "\n", newline="\n")
    return box


def axes(got, want):
    """Which of the two graded axes disagree on this journal."""
    marks = set()
    for a, b in zip(got, want):
        if a == b:
            continue
        if b[0] == "ak":
            marks.add("answers")
        elif b[0] in ("dg", "fin"):
            marks.add("holdings")
        else:
            marks.add("events")
    if len(got) != len(want):
        marks.add("events")
    return marks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=200)
    args = ap.parse_args()

    import tempfile
    import shutil

    texts = [(n, cases.PROGS[n]) for n in sorted(cases.PROGS)]
    texts += [("g%04d" % i, gen.text("field/%d" % i)) for i in range(args.count)]
    want = {n: harness.ref(t) for n, t in texts}

    scratch = pathlib.Path(tempfile.mkdtemp(prefix="gso-field-"))
    thin = []
    try:
        print("%-38s %6s %6s  %s" % ("cheat", "cases", "gen", "axis"))
        for path in sorted((ROOT / "cheat").glob("cheat-*.sh")):
            box = policy_of(path, scratch / path.stem)
            if box is None:
                continue
            hit_case = hit_gen = 0
            marks = set()
            for name, text in texts:
                try:
                    got = harness.run(text, box)
                except Exception:
                    got = []
                if got != want[name]:
                    if name in cases.PROGS:
                        hit_case += 1
                    else:
                        hit_gen += 1
                    marks |= axes(got, want[name])
            if path.stem in BY_ATTESTATION:
                print("%-38s %6s %6s  %s" % (path.stem, "-", "-",
                      "identical by design; rejected by an attestation, see cheat_report"))
                continue
            note = ",".join(sorted(marks)) or "NOTHING - this cheat is not separated at all"
            if hit_gen and hit_gen < 10:
                note += "   <- lottery: %d of %d generated journals" % (hit_gen, args.count)
                thin.append(path.stem)
            if not hit_gen and not hit_case:
                thin.append(path.stem)
            print("%-38s %6d %6d  %s" % (path.stem, hit_case, hit_gen, note))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    print("\n%d cheats wanting attention" % len(thin))
    for name in thin:
        print("  ", name)
    return 1 if thin else 0


if __name__ == "__main__":
    sys.exit(main())
