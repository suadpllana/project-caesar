"""Run the reference and the sealed model over a generated population and compare them.

Also reports what each family actually exercises: an unshaped family that never produces a
second survivor, never settles an open entry twice and never comes out ambiguous is not
testing the rules it was written for.
"""
import collections
import sys
import time

ROOT = "/home/user/project-caesar/tasks/widen-pin-bind"
sys.path.insert(0, ROOT + "/tests")
sys.path.insert(0, ROOT + "/tests/seal")
sys.path.insert(0, "/home/user/project-caesar/authoring/widen-pin-bind")

import gen  # noqa: E402
import model  # noqa: E402
import lab  # noqa: E402


def stats(lines, out):
    kinds = collections.Counter()
    for line in out:
        if line.startswith("res "):
            tail = line.rsplit(" ", 1)[1]
            kinds["res_" + (tail if tail in ("amb", "none") else "bind")] += 1
        elif line.startswith("pin "):
            kinds["pin"] += 1
        elif line.startswith("bind "):
            kinds["bind"] += 1
    return kinds


def main():
    seed = sys.argv[1] if len(sys.argv) > 1 else "agree"
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    run = lab.runner()
    bad = 0
    per_fam = collections.defaultdict(collections.Counter)
    clock = collections.defaultdict(float)
    for fam, name, lines in gen.programs(seed, per):
        text = "\n".join(lines) + "\n"
        t0 = time.time()
        got = run(text)
        clock[fam] += time.time() - t0
        t0 = time.time()
        want = model.expect(lines)
        clock[fam + "/model"] += time.time() - t0
        if got != want:
            bad += 1
            if bad <= 3:
                print("DIFFER", name)
                for a, b in zip(got, want):
                    if a != b:
                        print("   ref  ", a)
                        print("   model", b)
                        break
                print("   ref lines %d model lines %d" % (len(got), len(want)))
        per_fam[fam].update(stats(lines, want))
        per_fam[fam]["progs"] += 1
    print("disagreements:", bad)
    print("%-8s %6s %6s %6s %6s %6s  %8s %8s" % (
        "family", "progs", "bind", "amb", "none", "pins", "ref s", "model s"))
    for fam, _big in gen.FAMILIES:
        c = per_fam[fam]
        print("%-8s %6d %6d %6d %6d %6d  %8.2f %8.2f" % (
            fam, c["progs"], c["res_bind"], c["res_amb"], c["res_none"], c["pin"],
            clock[fam], clock[fam + "/model"]))


if __name__ == "__main__":
    main()
