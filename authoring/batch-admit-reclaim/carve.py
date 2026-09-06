"""Find, for each misreading, the smallest trace that separates it, and shrink it.

A hand-picked example that does not actually exercise the rule it is named for is
a false affordance, so no case here is written by hand: each one is searched for
mechanically, shrunk while the separation survives, and checked against the
sealed model before it is kept. The must-still-work cases are searched the same
way, against the property they are meant to hold rather than against a reading.

Usage: python3 authoring/batch-admit-reclaim/carve.py > tasks/.../tests/cases.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tasks", "batch-admit-reclaim", "authoring"))
sys.path.insert(0, os.path.join(ROOT, "tasks", "batch-admit-reclaim", "tests"))

import gen
import play
import readings

WORK = os.environ.get("WORK", "/tmp/bar-work")


def parts(text):
    head, reqs = [], {}
    order = []
    for line in text.strip().splitlines():
        b = line.split()
        if b[0] in ("pool", "block", "batch"):
            head.append(line)
        elif b[0] == "req":
            order.append(b[1])
            reqs[b[1]] = {"at": int(b[2]), "prompt": [], "emit": []}
        elif b[0] in ("prompt", "emit"):
            reqs[b[1]][b[0]] = [int(x) for x in b[2:]]
    return head, order, reqs


def build(head, order, reqs):
    out = list(head)
    for rid in order:
        out.append("req %s %d" % (rid, reqs[rid]["at"]))
    for rid in order:
        out.append("prompt %s %s" % (rid, " ".join(str(x) for x in reqs[rid]["prompt"])))
        out.append("emit %s %s" % (rid, " ".join(str(x) for x in reqs[rid]["emit"])))
    return "\n".join(out) + "\n"


def shrink(text, holds):
    head, order, reqs = parts(text)
    moved = True
    while moved:
        moved = False
        for rid in list(order):
            if len(order) == 1:
                break
            trial = build(head, [x for x in order if x != rid],
                          dict((k, v) for k, v in reqs.items() if k != rid))
            if holds(trial):
                head, order, reqs = parts(trial)
                moved = True
                break
        for rid in list(order):
            for field in ("emit", "prompt"):
                floor = 1 if field == "emit" else 1
                while len(reqs[rid][field]) > floor:
                    cut = dict((k, dict(v)) for k, v in reqs.items())
                    cut[rid][field] = cut[rid][field][:-1]
                    trial = build(head, order, cut)
                    if not holds(trial):
                        break
                    reqs = cut
                    moved = True
    return build(head, order, reqs)


def main(argv):
    ref = play.reference(os.path.join(WORK, "ref"))
    pool = [t for _, t in gen.batch("carve", 900)]
    found = []
    for label, files in sorted(readings.READINGS.items()):
        tree = play.build(os.path.join(WORK, "carve-%s" % label[:24]),
                          readings.merge(files))

        def holds(text, tree=tree):
            a = play.safe(ref, text)
            if not a or a[0][0] == "torn":
                return False
            return play.safe(tree, text) != a

        hit = None
        for text in sorted(pool, key=len):
            if holds(text):
                hit = text
                break
        if hit is None:
            sys.stderr.write("NO SEPARATOR for %s\n" % label)
            continue
        found.append((label, shrink(hit, holds)))
    for label, text in found:
        sys.stderr.write("%-52s %3d lines\n" % (label, len(text.strip().splitlines())))
    print(render(found))
    return 0


def render(found):
    out = []
    for label, text in found:
        out.append('    "%s": """\\\n%s""",' % (slug(label), text))
    return "\n".join(out)


def slug(label):
    keep = [c if c.isalnum() else "-" for c in label.lower()]
    s = "".join(keep)
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
