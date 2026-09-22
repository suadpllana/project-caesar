"""Time the reference and the exactly-correct binder without a memo, family by family.

The limit in the brief is for the whole graded set, so what matters is the total, and the two
scale families are what put a number on it. Output is flushed: a timing harness whose output
sits in a buffer behind the slow case looks exactly like a hang.
"""
import sys
import time

sys.path.insert(0, "/home/user/project-caesar/tasks/widen-pin-bind/tests")
sys.path.insert(0, "/home/user/project-caesar/authoring/widen-pin-bind")

import gen  # noqa: E402
import lab  # noqa: E402


def main():
    which = sys.argv[1]
    fams = sys.argv[2].split(",") if len(sys.argv) > 2 else ["deep", "wide"]
    per = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    overlay = lab.SOL if which == "ref" else "/home/user/project-caesar/authoring/widen-pin-bind/" + which
    run = lab.runner(overlay)
    whole = 0.0
    for fam, name, lines in gen.programs("timing", per):
        if fam not in fams:
            continue
        text = "\n".join(lines) + "\n"
        t0 = time.time()
        out = run(text)
        took = time.time() - t0
        whole += took
        print("%-10s %-12s %8.2f s  %5d lines" % (which, name, took, len(out)), flush=True)
    print("%-10s TOTAL %8.2f s" % (which, whole), flush=True)


if __name__ == "__main__":
    main()
