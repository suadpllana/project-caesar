"""How much of the graded population does each wrong reading actually move?

Separation says an enumerated case catches a reading. This says whether the generated
population would catch it too, which is the number that matters when a submission has
fitted the shipped examples: under all-or-nothing grading a reading that moves one program
in three hundred still scores 0, but a reading that moves none is a reading the population
does not exercise at all, and the families are shaped until every one of them moves.

Usage: python authoring/pull-check-stale/ablate.py [per-family] [seeds]
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import readings                                     # noqa: E402

sys.path.insert(0, str(HERE.parent.parent / "tasks" / "pull-check-stale" / "tests"))
import gen                                          # noqa: E402


def main(argv):
    per = int(argv[1]) if len(argv) > 1 else 6
    seeds = argv[2].split(",") if len(argv) > 2 else ["a1", "a2"]
    pop = []
    for seed in seeds:
        pop.extend(gen.programs(seed, per))
    print("population %d programs over %d families" % (len(pop), len(gen.FAMILIES)))
    ref = readings.REFERENCE
    base = {}
    for pid, text in pop:
        base[pid + text] = readings.run(ref, text)
    rows = []
    for name, files in sorted(readings.READINGS.items()):
        alt = str(readings.policy_dir_for(files))
        moved = 0
        crash = 0
        for pid, text in pop:
            try:
                got = readings.run(alt, text)
            except Exception:
                crash += 1
                continue
            if got != base[pid + text]:
                moved += 1
        rows.append((moved + crash, name, moved, crash))
        print("  %-22s moves %4d/%d (%5.1f%%)%s"
              % (name, moved + crash, len(pop), 100.0 * (moved + crash) / len(pop),
                 "  raised on %d" % crash if crash else ""))
    rows.sort()
    dead = [r for r in rows if r[0] == 0]
    print("weakest: %s" % ", ".join("%s %d" % (r[1], r[0]) for r in rows[:3]))
    if dead:
        print("NOT EXERCISED by the generated population: %s"
              % ", ".join(r[1] for r in dead))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
