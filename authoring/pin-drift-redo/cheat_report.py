#!/usr/bin/env python3
"""Which graded case catches each semantic cheat, and how much of the population it moves.

A reward of 0 is not evidence: a cheat can score 0 because its patch never fired, because it
crashed, or because it was caught by a case that has nothing to do with the rule it breaks. The
first is how a cheat suite reports clean zeroes while testing the shipped tree; the third is how
a failure stops naming a rule. So this asserts the layer: for every semantic cheat, the
enumerated case named for it must be one of the cases it fails.

The isolation probes are not judged here - their effect is on the verifier, not on a trace - and
go through authoring/host_trial.py instead.

    python3 -u authoring/pin-drift-redo/cheat_report.py
"""
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

cases, gen, model = lab.sealed()

# Each semantic cheat, and the enumerated case whose name says which rule it breaks.
CAUGHT_BY = {
    "take-at-open": "take-first-touch",
    "retake-close-only": "retake-shows-in-read",
    "no-close-retake": "retake-at-close",
    "abort-on-move": "retake-at-close",
    "copy-takes-number": "redo-through-copy",
    "copy-takes-standing": "copy-holds-own",
    "copy-names-one-key": "read-then-copy",
    "raw-copies-held": "raw-ignores-own",
    "raw-fixes": "raw-follows-basis",
    "bmp-no-retake": "bmp-moves-copy",
    "read-not-fixed": "read-fixes",
    "read-writes": "read-no-write",
    "undo-restores-numbers": "undo-owes-after-mark",
    "undo-no-mark-nothing": "undo-no-mark",
    "cond-when-run": "cond-holds-later",
    "cond-at-end": "cond-at-its-place",
    "cond-fail-aborts": "cut-and-carry-on",
    "cond-never-cuts": "cut-and-carry-on",
    "cut-keeps-values": "cut-feeds-next",
    "cut-stops-testing": "nest-outer-next",
    "cond-no-mark-ok": "cond-no-mark",
    "lim-strict": "lim-at-n",
    "publish-high-first": "publish-order",
    "publish-skips-unchanged": "publish-unchanged",
    "publish-run-time-set": "publish-drops-key",
    "drop-writes": "drop-writes-nothing",
}

ROUNDS = 40


def population():
    out = []
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(ROUNDS):
            rng = random.Random("report|%s|%d" % (fam, i))
            out.append(("%s-%d" % (fam, i), gen.BUILD[fam](rng)))
    return out


def forgery_layer(truth, hand, wild, want):
    """Apply cheat-forge-hand to a staged tree and count what it gets right and wrong."""
    import subprocess
    import tempfile
    here = lab.tree(None)
    script = (lab.TASK / "cheat" / "cheat-forge-hand.sh").read_text(encoding="utf-8")
    script = script.replace("/app/led/", str(here / "led") + "/")
    where = Path(tempfile.mkdtemp()) / "forge.sh"
    where.write_text(script, encoding="utf-8")
    subprocess.run(["bash", str(where)], check=True, capture_output=True)
    right = sum(1 for name, text in hand if lab.run_text(here, text) == truth[name])
    wrong = sum(1 for name, text in wild if lab.run_text(here, text) != want[name])
    return right, len(hand), wrong, len(wild)


def main():
    for build in emit.READING_BUILDERS:
        build()
    truth = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    hand = [(name, "\n".join(cases.prog(name))) for name in cases.ORDER]
    wild = [(name, "\n".join(lines)) for name, lines in population()]
    want = {name: model.expect(text.split("\n")) for name, text in wild}

    bad = []
    print("%-24s %-22s %6s %7s" % ("cheat", "named case", "cases", "moved"), flush=True)
    for name in sorted(emit.READINGS):
        here = lab.files_tree(emit.READINGS[name])
        missed = [case for case, text in hand if lab.run_text(here, text) != truth[case]]
        moved = sum(1 for case, text in wild if lab.run_text(here, text) != want[case])
        named = CAUGHT_BY.get(name)
        ok = named in missed
        if not ok:
            bad.append((name, named, missed[:4]))
        print("%-24s %-22s %6d %6.1f%% %s" %
              (name, named or "-", len(missed), 100.0 * moved / len(wild),
               "" if ok else "NOT CAUGHT BY ITS CASE"), flush=True)
    # The forgery is not a reading: what it has to prove is that it passes every hand
    # program and still fails, which is the nonce population doing the work and not the
    # enumerated set. A forgery that crashed early would score 0 and prove nothing.
    forged = forgery_layer(truth, hand, wild, want)
    print("\nforge-hand reproduces %d of %d hand programs and gets %d of %d generated ones wrong"
          % forged, flush=True)
    if forged[0] != forged[1] or forged[2] != forged[3]:
        bad.append(("forge-hand", "hand programs and nonce programs", []))

    print()
    if bad:
        for name, named, missed in bad:
            print("%s: %s does not fail it; fails %s" % (name, named, missed))
        return 1
    print("every semantic cheat is caught by the enumerated case named for it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
