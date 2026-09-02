"""Score one staged tree, in a child process.

A probe that calls os._exit, forks, or walks the filesystem has to be contained: run in
the reporting process it takes the report down with it and the sweep comes back empty and
exit 0, which reads as a clean suite. Every tree is graded here instead, one child each.

    python3 authoring/score_one.py <tree> <generated-count> <seed>
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import gen  # noqa: E402
import harness  # noqa: E402
import oracle  # noqa: E402
import scen  # noqa: E402


def bad(tree, streams):
    got = harness.drive(tree, streams)
    out = []
    for name, text in streams:
        want = oracle.play(text)
        g = got[name]
        if (g["err"]
                or oracle.rounds([list(x) for x in g["log"]]) != oracle.rounds([list(x) for x in want["log"]])
                or g["sheet"] != want["sheet"]):
            out.append(name)
    return out


def main():
    tree, count, seed = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    res = {"cases": bad(tree, list(scen.STREAMS)), "gen": bad(tree, gen.batch(seed, count))}
    sys.stdout.write("QDRSCORE " + json.dumps(res) + "\n")


main()
