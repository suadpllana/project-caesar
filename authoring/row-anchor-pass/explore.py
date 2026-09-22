"""For every emitted cheat: which enumerated programs it fails, and how much of a generated
population it moves. Exploration only - cheat_report.py is the assertion."""
import json
import random
import sys

import emit
import lab

cases, gen, model = lab.sealed()
gt = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
emit.main()
SAMPLE = int(sys.argv[1]) if len(sys.argv) > 1 else 12
pop = []
for fam, big in gen.FAMILIES:
    if big:
        continue
    for i in range(SAMPLE):
        rng = random.Random("explore|%s|%d" % (fam, i))
        lines = gen.MAKERS[fam](rng)
        pop.append((fam, lines, model.expect(lines)))
names = sys.argv[2:] or sorted(emit.BUILT)
for name in names:
    if name.startswith("probe-") or name in ("slow-push", "slow-lazy", "forge-hand"):
        continue
    here = lab.tree(files=emit.BUILT[name])
    failed = []
    for case in cases.ORDER:
        try:
            got = here(cases.prog(case))
        except Exception:
            got = None
        if got != gt[case]:
            failed.append(case)
    moved = 0
    byfam = {}
    for fam, lines, want in pop:
        try:
            got = here(lines)
        except Exception:
            got = None
        if got != want:
            moved += 1
            byfam[fam] = byfam.get(fam, 0) + 1
    print("%-22s %2d cases  %3d/%d moved  %s" % (name, len(failed), moved, len(pop),
          ",".join(failed[:6]) + (" ..." if len(failed) > 6 else "")), flush=True)
