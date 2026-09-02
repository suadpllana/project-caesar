"""No graded comparison may come down to a name the submission chose.

`share-register-screen` shipped two correct implementations that disagreed on
three registers in twelve hundred, because each had invented a key for a synthetic
row and the two sorted either side of the real ones. Nothing in the brief or the
verifier mentioned that key. That is a run-audit rejection waiting to happen, and
no amount of reasoning about the specification finds it.

Here the claim is that there is nothing to invent: every comparison the machine
makes is over the plan's own names and its own integers. The seal order is
(gather name, bucket index), both of which come out of the plan; bucket indexes
come from stamp arithmetic; accounts and bounds are integers. Two checks stand
behind that claim rather than asserting it.

  The only string constants a decision file may hold are the five node kinds. A
  new one is a name the submission invented, and the next question is whether it
  reaches a comparison.

  The mirror variant is required to agree event for event. `ok-key-order` sorts
  the ready buckets through an explicit key rather than tuple order, which is the
  one place a comparison could have picked up a type or an ordering the reference
  got by accident.

A NON-FINDING, recorded because the first version of this file reported it as a
fault: renaming the nodes in a plan does change its trace, and legitimately. The
machine serves the lexicographically first node holding anything and records seals
in name order, both stated in the brief, so the names are input rather than
implementation. What matters is that no name comes from the submission.
"""

import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "authoring"))
sys.path.insert(0, str(ROOT / "tests"))

import cases
import gen
import harness

KINDS = {"src", "relay", "lift", "gather", "sink"}
POL = ("emit.py", "route.py", "due.py", "pick.py")


def strings(path):
    out = set()
    tree = ast.parse(path.read_text())
    doc = ast.get_docstring(tree, clean=False)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if doc is not None and node.value == doc:
                continue
            out.add(node.value)
    return out


def main():
    bad = 0
    for name in POL:
        for where in (ROOT / "solution", ROOT / "environment" / "app_src" / "flow"):
            p = where / name
            if not p.is_file():
                continue
            loose = sorted(s for s in strings(p) if s not in KINDS)
            if loose:
                bad += 1
                print("%s/%s holds string constants that are not node kinds: %s"
                      % (where.name, name, loose))

    mirror = ROOT / "authoring" / "variants" / "ok-key-order"
    if not mirror.is_dir():
        print("no mirror variant; run make_variants.py first")
        return 1
    plans = [(n, cases.PLANS[n]) for n in sorted(cases.PLANS)]
    plans += [(nm, gen.text(p)) for nm, p in gen.batch("tiecheck", 200)]
    moved = 0
    ref = harness.tree(str(ROOT / "solution"))
    alt = harness.tree(str(mirror))
    try:
        for nm, text in plans:
            a = harness.drive(ref, text)
            b = harness.drive(alt, text)
            if a["tr"] != b["tr"] or a["sk"] != b["sk"]:
                moved += 1
                print("%s: the mirror variant disagrees" % nm)
                if moved > 3:
                    break
    finally:
        import shutil
        shutil.rmtree(ref.parent, ignore_errors=True)
        shutil.rmtree(alt.parent, ignore_errors=True)
    print("%d loose names, %d of %d plans moved by the mirror variant"
          % (bad, moved, len(plans)))
    return 1 if (bad or moved) else 0


if __name__ == "__main__":
    sys.exit(main())
