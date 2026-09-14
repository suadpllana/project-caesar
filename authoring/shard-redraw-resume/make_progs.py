"""Write the four programs the agent's tree ships, and search for the worked example.

The brief quotes one line of one shipped program with the value it should have. That line is an
oracle for every wrong reading it happens to decide, so it is searched for rather than chosen:
of the lines where the shipped driver and the reference disagree, take one that the fewest
wrong readings also disagree on.

    python3 authoring/shard-redraw-resume/make_progs.py           write the programs
    python3 authoring/shard-redraw-resume/make_progs.py --pick    search for the example line
"""
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "shard-redraw-resume"
RUNS = TASK / "environment" / "app_src" / "runs"
sys.path.insert(0, str(HERE))

import lab  # noqa: E402

PROGS = {
    "small": """
        rows 44
        seed 61
        rank 2
        micro 2
        accum 2
        ckpt 2
        grow 3
        scale 2
        epochs 2
        nf 26
        run 6
        kill
        back 3
        run 5
    """,
    "swap": """
        rows 180
        seed 74
        rank 3
        micro 2
        accum 3
        ckpt 3
        grow 4
        scale 3
        epochs 2
        nf 41
        nf 118
        nf 7
        run 9
        back 2
        run 4
        kill
        back 5
        run 8
        kill
        run 6
    """,
    "wide": """
        rows 60000000
        seed 88
        rank 4
        micro 8
        accum 4
        ckpt 4
        grow 3
        scale 2
        epochs 1
        nf 51204833
        nf 9117402
        nf 30556781
        run 400
        kill
        back 2
        run 400
    """,
    "deep": """
        rows 10800
        seed 93
        rank 3
        micro 2
        accum 2
        ckpt 2
        grow 3
        scale 1
        epochs 30
        run 25
    """,
}


def deep_tail():
    out = []
    for i in range(400):
        out.append("kill" if i % 3 else "back %d" % (1 + (i % 4)))
        out.append("run 25")
    return out


def lines(name):
    body = [" ".join(l.split()) for l in PROGS[name].strip().splitlines()]
    return body + (deep_tail() if name == "deep" else [])


def write():
    RUNS.mkdir(parents=True, exist_ok=True)
    for name in PROGS:
        path = RUNS / (name + ".txt")
        path.write_text("\n".join(lines(name)) + "\n", encoding="utf-8", newline="\n")
        assert "\r" not in path.read_text(encoding="utf-8")
        print("wrote %s (%d ops)" % (path, len(lines(name))))


def pick():
    sys.path.insert(0, str(HERE))
    import emit  # noqa: E402
    readings = {}
    for build in emit.SEMANTIC:
        emit.BUILT.clear()
        build()
        readings.update(emit.BUILT)
    room = pathlib.Path(tempfile.mkdtemp(prefix="srr-pick-"))
    prog = room / "small.txt"
    prog.write_text("\n".join(lines("small")) + "\n", encoding="utf-8", newline="\n")
    ref = lab.run(lab.tree(TASK / "solution"), prog)
    ship = lab.run(lab.tree(), prog)
    alts = {}
    for name, files in readings.items():
        over = pathlib.Path(tempfile.mkdtemp(prefix="srr-alt-"))
        for part, src in files.items():
            (over / part).write_text(src, encoding="utf-8", newline="\n")
        alts[name] = lab.run(lab.tree(over), prog)

    print("reference %d lines, shipped %d lines" % (len(ref), len(ship)))
    for i in range(min(len(ref), len(ship))):
        if ref[i] == ship[i]:
            continue
        decided = [n for n, out in alts.items()
                   if i >= len(out) or out[i] != ref[i]]
        print("line %3d  shipped %-28s should be %-28s decides %d %s"
              % (i + 1, ship[i], ref[i], len(decided), sorted(decided)))


if __name__ == "__main__":
    if "--pick" in sys.argv:
        pick()
    else:
        write()
