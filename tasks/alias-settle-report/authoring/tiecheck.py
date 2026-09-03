"""No graded value may come down to a name the machine or a submission chose.

The one name nothing states is the cell's root: Book.weld picks it by weight, and
a cell's root is what span returns, what the difference set is lifted onto and
what the readiness test is asked about. If a graded row moved when that choice
moved, two correct implementations could disagree over a symbol the instruction
never mentions, which is a run audit rejection rather than a bug.

So the mirror is run: the same reference over the same sets, with the frozen weld
picking the other root every time, and every row has to come back identical.
"""

import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))

import cases
import gen
import harness

OLD = """        if self.wt[ra] < self.wt[rb]:
            ra, rb = rb, ra"""
NEW = """        if ra < rb:
            ra, rb = rb, ra"""


def mirror():
    box = tempfile.mkdtemp(prefix="tie-")
    tree = os.path.join(box, "app_src")
    shutil.copytree(os.path.join(TASK, "environment", "app_src"), tree)
    for name in ("rch.py", "hold.py", "card.py", "seq.py"):
        shutil.copyfile(os.path.join(TASK, "solution", name),
                        os.path.join(tree, "bind", name))
    path = os.path.join(tree, "bind", "bk.py")
    with open(path) as fh:
        body = fh.read()
    if OLD not in body:
        raise SystemExit("the weld tie-break is not where tiecheck expects it")
    with open(path, "w", newline="\n") as fh:
        fh.write(body.replace(OLD, NEW))
    return box, tree


def main(argv):
    rounds = int(argv[1]) if len(argv) > 1 else 400
    box, tree = mirror()
    plain = harness.Rig(os.path.join(TASK, "solution"))
    texts = [cases.SETS[n] for n in sorted(cases.SETS)]
    texts += [gen.one("tie:%d" % i) for i in range(rounds)]
    off = 0
    for text in texts:
        if plain.run(text) != harness.drive(tree, text):
            off += 1
    plain.close()
    shutil.rmtree(box, ignore_errors=True)
    if off:
        print("%d of %d sets moved when the root moved" % (off, len(texts)))
        return 1
    print("no graded row moved when the cell root moved (%d sets)" % len(texts))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
