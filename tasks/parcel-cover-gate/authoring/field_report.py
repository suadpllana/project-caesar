"""What each cheat gets wrong, and on how many feeds.

Two numbers per cheat and both are worth reading before a contract is frozen.

Which of the two graded things it moves. A graded thing that separates no cheat
is pure liability: it cannot catch a wrong answer and it can still fail a right
one. Both of the ones here - the rows and the closing pictures - have to be
carried by something.

How rare the disagreement is. A reading that moves a handful of feeds in three
hundred is a lottery ticket rather than a test of expertise: under all-or-nothing
grading it is indistinguishable from bad luck, and the honest move is either to
widen the generated space until it bites properly or to accept it is a fence
rather than an axis. Anything in single-figure percentages here should be looked
at rather than shrugged at.
"""

import os
import shutil
import subprocess
import sys
import tempfile

import lab


def apply(script, where):
    run = subprocess.run(["bash", str(script)], capture_output=True, text=True,
                         env=dict(os.environ, APP_DIR=where), timeout=300)
    if run.returncode != 0:
        raise RuntimeError(run.stderr[-400:])


def main(argv):
    count = int(argv[argv.index("--count") + 1]) if "--count" in argv else 200
    feeds = lab.named()
    feeds.update(lab.made("field-report", count))
    hold = tempfile.mkdtemp(prefix="pcg-field-")
    try:
        want = lab.play(lab.tree(os.path.join(hold, "ref"), lab.reference()), feeds)
        names = sorted(feeds)
        print("%-26s %6s %6s %6s" % ("cheat", "feeds", "rows", "tails"))
        for script in sorted((lab.ROOT / "cheat").glob("*.sh")):
            where = lab.tree(os.path.join(hold, script.stem), lab.shipped())
            try:
                apply(script, where)
                got = lab.play(where, feeds)
            except Exception as exc:
                print("%-26s  could not be driven: %s" % (script.stem, exc))
                continue
            off = [n for n in names if got[n] != want[n]]
            rows = sum(1 for n in names if got[n]["rows"] != want[n]["rows"])
            tail = sum(1 for n in names if got[n]["tail"] != want[n]["tail"])
            print("%-26s %5d%% %6d %6d"
                  % (script.stem, (100 * len(off)) // len(names), rows, tail))
    finally:
        shutil.rmtree(hold, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
