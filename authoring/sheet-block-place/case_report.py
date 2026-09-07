"""Assert that every named reading is caught by an enumerated case, not only by the
generated families. A reading separated only by generation is a rule with no hand case
behind it, which is exactly what the quality review reads for."""

import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "tasks" / "sheet-block-place" / "tests"))

import cases  # noqa: E402
import harness  # noqa: E402
import readings  # noqa: E402


def main():
    names = sorted(cases.CASES)
    texts = [cases.CASES[n] for n in names]
    base = harness.run_with(str(readings.REF), texts, limit=600)

    trees = [("shipped-engine", str(readings.SHIPPED), "the tree as it ships")]
    made = []
    for name, rel, old, new, want in readings.PATCHES:
        home = readings.make(name, rel, old, new)
        made.append(home)
        trees.append((name, str(home), want))

    bad = []
    print("%-26s %-34s %s" % ("reading", "named case catches it", "cases catching it"))
    for name, tree, want in trees:
        got = harness.run_with(tree, texts, limit=600)
        hits = [names[i] for i in range(len(names))
                if isinstance(got[i], dict) or got[i] != base[i]]
        named = "-" if want == "the tree as it ships" else ("yes" if want in hits else "NO")
        if named == "NO":
            bad.append((name, want))
        if not hits:
            bad.append((name, "no case at all"))
        print("%-26s %-34s %d  %s" % (name, "%s (%s)" % (named, want), len(hits),
                                      ", ".join(hits[:3])))

    for home in made:
        shutil.rmtree(home, ignore_errors=True)
    if bad:
        print("\nUNSEPARATED:")
        for name, want in bad:
            print("  %s -> %s" % (name, want))
        return 1
    print("\nevery reading is caught by the case that names it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
