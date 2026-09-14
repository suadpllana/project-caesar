"""Print an enumerated case's program and the trace the reference gives it.

    python3 authoring/shard-redraw-resume/show.py <case-name> [more names...]
    python3 authoring/shard-redraw-resume/show.py --all      one summary line per case
"""
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "shard-redraw-resume"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(ROOT / "authoring" / "shard-redraw-resume"))

import cases  # noqa: E402
import lab  # noqa: E402


def trace(here, room, name):
    path = room / (name + ".txt")
    path.write_text("\n".join(cases.ops(name)) + "\n", newline="\n")
    return lab.run(here, path)


def main():
    here = lab.tree(TASK / "solution")
    room = pathlib.Path(tempfile.mkdtemp(prefix="srr-show-"))
    if "--all" in sys.argv:
        for name in cases.ORDER:
            got = trace(here, room, name)
            kinds = {}
            for line in got:
                kinds[line.split()[0]] = kinds.get(line.split()[0], 0) + 1
            print("%-13s %3d lines  %s" % (name, len(got),
                  " ".join("%s=%d" % kv for kv in sorted(kinds.items()))))
        return
    for name in sys.argv[1:]:
        print("== %s" % name)
        print("   " + " | ".join(cases.ops(name)))
        for line in trace(here, room, name):
            print("   " + line)


if __name__ == "__main__":
    main()
