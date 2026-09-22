#!/usr/bin/env python3
"""Which graded case catches each semantic cheat, and how much of the population it moves.

A reward of 0 is not evidence: a cheat can score 0 because its patch never fired, because it
crashed, or because it was caught by a case that has nothing to do with the rule it breaks. So
this asserts the layer: for every cheat, the enumerated case named for it must be one of the
cases it fails, and it reports how much of a generated sample each one moves.

The isolation probes are not judged here - their effect is on the verifier, not on a printout -
and go through host_trial.py instead.

    python3 -u authoring/owed-check-rewind/cheat_report.py
"""
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

# Each semantic cheat, and the enumerated case whose name says which rule it breaks.
CAUGHT_BY = {
    "key-upsert": "key-dup",
    "missing-raises": "miss-noop",
    "min-null-fails": "min-null",
    "min-inclusive": "min-floor",
    "row-at-end": "row-at-write",
    "restrict-at-end": "restrict-at-once",
    "noaction-at-delete": "noaction-at-end",
    "walk-breadth": "walk-depth-first",
    "walk-listed-early": "walk-listed-late",
    "walk-reverse": "walk-decl-order",
    "touch-key-order": "walk-touch-order",
    "imm-touch-first": "imm-order",
    "deferred-no-action": "action-deferred",
    "eager-mend": "lazy-mend",
    "rewrite-remakes": "rewrite-keeps-place",
    "name-children": "side-parent",
    "side-eager": "side-holders-moved",
    "side-merged": "side-both",
    "deleted-keeps": "deleted-row-clears",
    "order-by-record": "order-decl",
    "newest-first": "order-within",
    "failset-clears": "failset-atomic",
    "set-judges-all": "set-named-only",
    "commit-no-list": "commit-lists",
    "rollback-no-list": "rollback-lists",
    "mode-kept": "rewind-mode",
    "modes-carry": "modes-per-txn",
    "nondeferrable-ok": "set-nondeferrable",
    "immediate-nondeferrable-ok": "set-immediate-nondeferrable",
    "recompute-ledger": "rewind-cleared-back",
    "place-not-restored": "replace-place",
    "list-moved": "replace-place",
    "release-keeps-later": "release-drops-later",
    "rollback-drops-it": "rewind-keeps",
    "shadow-oldest": "shadow",
    "unknown-ok": "error-unknown",
    "aborted-acts": "abort-ignored",
    "aborted-commits": "abort-commit",
    "commit-fail-keeps": "commit-fail",
    "slow-copy": None,          # exactly correct; only the clock separates it
    "slow-scan": None,
    "slow-ledger": None,
    "const-ok": "key-dup",
    "forge-hand": None,         # passes every enumerated program by construction
}

SAMPLE = 16


def main():
    cases, gen, model = lab.sealed()
    gt = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))

    for build in emit.READING_BUILDERS:
        build()
    for build in (emit.slow_copy, emit.slow_scan, emit.slow_ledger, emit.const_ok,
                  emit.forge_hand):
        build()

    pop = []
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(SAMPLE):
            rng = random.Random("report|%s|%d" % (fam, i))
            lines = gen.build(fam, rng)
            pop.append((fam, lines, model.expect(lines)))

    bad = 0
    per_family = {}
    for name in sorted(CAUGHT_BY):
        files = emit.BUILT[name]
        here = lab.tree(files=files)
        failed = []
        for case in cases.ORDER:
            lines = cases.prog(case)
            if lab.run_text(here, "\n".join(lines) + "\n") != gt[case]:
                failed.append(case)
        moved = 0
        fam_moved = {}
        for fam, lines, want in pop:
            if lab.run_text(here, "\n".join(lines) + "\n") != want:
                moved += 1
                fam_moved[fam] = fam_moved.get(fam, 0) + 1
        per_family[name] = fam_moved
        want = CAUGHT_BY[name]
        if want is None:
            verdict = "no enumerated case, by design" if not failed else \
                "UNEXPECTED: fails %s" % failed[:3]
            if failed:
                bad += 1
        elif want in failed:
            verdict = "caught by %s" % want
        else:
            verdict = "NOT CAUGHT by %s (fails %s)" % (want, failed[:3] or "nothing")
            bad += 1
        print("%-20s %2d/%d enumerated fail, %3d/%d generated moved   %s"
              % (name, len(failed), len(cases.ORDER), moved, len(pop), verdict), flush=True)

    print("\n%d findings" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
