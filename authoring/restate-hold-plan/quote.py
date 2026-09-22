#!/usr/bin/env python3
"""Which line of the sample plan may the brief quote without handing over a rule? Never ships.

The brief quotes one line of the plan for /app/pipes/small.txt, so a solver can check the output
format against something. A quoted line is evidence, and evidence that settles a wrong reading is
an oracle for that rule (CLAUDE.md, reach-pair-sweep: search for the example, do not choose it).
This prints, for every line of the correct plan, whether the shipped planner gets it right and
which wrong readings would print that line differently or drop it. The line to quote is one the
shipped planner gets wrong and that no reading of a load-bearing rule changes.

    python3 -u authoring/restate-hold-plan/quote.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402


def main():
    _cases, _gen, model = lab.sealed()
    text = (lab.SRC / "pipes" / "small.txt").read_text(encoding="utf-8")
    want = model.expect(text)
    shipped = lab.run_text(lab.tree(), text)
    emit.OUT.mkdir(exist_ok=True)
    for build in emit.READING_BUILDERS:
        build()
    plans = {name: lab.run_text(lab.tree(files=files), text)
             for name, files in emit.READINGS.items()}
    print("shipped planner prints %d lines, the plan has %d" % (len(shipped), len(want)))
    for k, line in enumerate(want):
        head = " ".join(line.split()[:3])
        movers = []
        for name, got in plans.items():
            same = [g for g in got if " ".join(g.split()[:3]) == head]
            if same != [line]:
                movers.append(name)
        print("%2d %-24s shipped:%-6s moved by: %s"
              % (k, line, "right" if line in shipped else "WRONG", ", ".join(movers) or "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
