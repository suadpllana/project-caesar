"""Apply every cheat to a staged tree and say which enumerated case catches it.

A cheat that dies on an import error has been rejected by nothing, so the failing case
is printed rather than the bare verdict. A cheat that passes every case is either a
correct implementation or a hole in the enumerated set, and the generated column is what
tells you which.

    python3 authoring/cheat_report.py [generated-count]
"""

import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import gen  # noqa: E402
import harness  # noqa: E402
import oracle  # noqa: E402
import scen  # noqa: E402

BASH = "/bin/bash"


def apply(script, tree):
    r = subprocess.run([BASH, str(script)], env={"APP": str(tree), "PATH": "/usr/bin:/bin"},
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("cheat %s exited %d: %s" % (script.name, r.returncode, r.stderr[:400]))


def score(tree, streams, want):
    got = harness.drive(tree, streams)
    bad = []
    for name, _ in streams:
        g = got[name]
        if g["err"] or g["log"] != want[name]["log"] or g["state"] != want[name]["state"]:
            bad.append(name)
    return bad


def main(argv):
    count = int(argv[1]) if len(argv) > 1 else 120
    cases = scen.cases()
    rand = gen.build("report", count)
    want_c = {n: oracle.play(t) for n, t in cases}
    want_g = {n: oracle.play(t) for n, t in rand}

    rows = []
    for label, overlay in (("REFERENCE", TASK / "solution"), ("shipped", None)):
        tree = harness.stage(TASK / "environment" / "app_src", overlay)
        rows.append((label, score(tree, cases, want_c), score(tree, rand, want_g)))

    for script in sorted((TASK / "cheat").glob("*.sh")):
        tree = harness.stage(TASK / "environment" / "app_src", None)
        apply(script, tree)
        rows.append((script.stem.replace("cheat-", ""),
                     score(tree, cases, want_c), score(tree, rand, want_g)))

    print("%-18s %-9s %-11s  %s" % ("", "cases", "generated", "first case that catches it"))
    for name, bc, bg in rows:
        print("%-18s %3d/%-5d %4d/%-6d %s"
              % (name, len(cases) - len(bc), len(cases), count - len(bg), count,
                 bc[0] if bc else ("-" if bg else "NOTHING CATCHES IT")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
