#!/usr/bin/env python3
"""Do the sealed model and every correct implementation print the same lines?

Two implementations written apart agreeing on a large generated population is the evidence
that the contract has one meaning; a disagreement is either a coding slip or a sentence that
two careful readers read two ways, and the second kind goes into the instruction.

    python3 -u authoring/owed-check-rewind/agree.py [seeds] [per] [dir ...]

With no directories it compares the model against solution/ and both variants.
"""
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

cases, gen, model = lab.sealed()


def main(argv):
    seeds = int(argv[0]) if argv else 4
    per = int(argv[1]) if len(argv) > 1 else 36
    dirs = [Path(a) for a in argv[2:]] or [
        p for p in (lab.SOL, HERE / "variants" / "ok-journal", HERE / "variants" / "ok-queue")
        if any((p / part).is_file() for part in lab.PARTS)]
    trees = {d.name: lab.tree(policy=d) for d in dirs}
    bad = 0
    total = 0
    spent = {n: 0.0 for n in trees}
    for s in range(seeds):
        for fam, name, lines in gen.programs("agree%d" % s, per):
            want = model.expect(lines)
            text = "\n".join(lines) + "\n"
            for label, here in trees.items():
                t = time.time()
                got = lab.run_text(here, text)
                spent[label] += time.time() - t
                if got != want:
                    bad += 1
                    first = next((i for i, (a, b) in enumerate(zip(got, want)) if a != b),
                                 min(len(got), len(want)))
                    print("DIFFER %-12s %s/%s line %d: got %r want %r"
                          % (label, s, name, first, (got[first:first + 1] or ["<end>"])[0][:90],
                             (want[first:first + 1] or ["<end>"])[0][:90]), flush=True)
            total += 1
    for label in trees:
        print("%-12s %.1fs over %d programs" % (label, spent[label], total))
    if cases is not None:
        for name in cases.ORDER:
            want = model.expect(cases.prog(name))
            for label, here in trees.items():
                if lab.run_text(here, "\n".join(cases.prog(name)) + "\n") != want:
                    bad += 1
                    print("DIFFER %-12s hand case %s" % (label, name))
    print("%d disagreements" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
