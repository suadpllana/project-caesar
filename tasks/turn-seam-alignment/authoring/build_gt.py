#!/usr/bin/env python3
"""Generate tests/gt.json from the reference solution, refusing to write anything the
sealed oracle has not confirmed first.

The reference loop is run over every scenario. For each one the naive replay in
tests/oracle.py - its own tokenizer, its own template, its own network, a full encode of
every render and no cache anywhere - is asked what the trainer should receive. Every
token of every episode, every trainable span, the forward count and the lifecycle trace
have to agree before the scenario is recorded. If they disagree the reference is wrong,
the oracle is wrong, or the two have drifted apart, and none of those may be papered over
by writing the reference's answer down as the truth.

The character meter is recorded as a window rather than as a number, and neither end of
it comes from the reference.

The floor is what the exact reading of the resume condition costs - resume at the last
position no symbol of the vocabulary can straddle. No implementation that obeys the rule
the instruction states can hand the tokenizer less than that, so a run under the floor
resumed somewhere that is only a boundary for the text it happened to be looking at, or
never encoded the render through the tokenizer at all. The oracle's count of the
characters that were not in the previous render sits under the floor and is checked
against it: that count is what a private copy of the encoder pays, and it has to be
strictly below the floor somewhere or the meter would accept one.

The ceiling is the most expensive of the one-sided resume tests in authoring/policies.py,
measured through the same harness the reference goes through. Those are the answers a
solver reaches when they see one half of the protection condition and not the other; both
are correct, they disagree with each other and with the reference on nine of the twelve
scenarios, and a verifier that demanded any one of those numbers would be grading which
reading a solver happened to settle on. Every alternative correct solution in
authoring/variants/ has to sit inside the window, and this refuses to write a ceiling that
has drifted up far enough to admit the answer the task does reject - resuming only on
characters that take part in no merge at all.

Usage:  python3 authoring/build_gt.py
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "authoring"))
sys.path.insert(0, str(TASK / "tests"))

import emit  # noqa: E402
import harness  # noqa: E402
import oracle  # noqa: E402
import policies  # noqa: E402
import scen  # noqa: E402

FIELDS = ("enc_calls", "fwd", "trace", "ids", "spans")


def as_spans(raw):
    return {k: [list(x) for x in v] for k, v in raw.items()}


def cost(variant: Path) -> dict:
    """Characters handed to the tokenizer by one implementation, per scenario."""
    data = harness.run(str(variant))
    if data.get("errors"):
        raise SystemExit("%s raised: %s" % (variant.name, sorted(data["errors"])))
    return {name: rep["enc_chars"] for name, rep in data["reports"].items()}


def mutated(swaps: dict, dest: Path) -> Path:
    """A copy of the reference with one anchored block replaced."""
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("inc.py", "store.py", "ep.py", "rec.py"):
        (dest / name).write_text((TASK / "solution" / "ref" / name).read_text())
    src = (dest / "inc.py").read_text()
    for old, new in swaps.items():
        if old not in src:
            raise SystemExit("anchor not found in reference inc.py")
        src = src.replace(old, new, 1)
    (dest / "inc.py").write_text(src)
    return dest


def main() -> int:
    emit.write_variants()

    data = harness.run("solution/ref")
    if data.get("errors"):
        for name, err in data["errors"].items():
            print("reference failed on", name, "\n", err)
        return 1

    ceilings = [cost(TASK / "authoring" / "variants" / ("ok-" + n))
                for n in policies.CEILING]
    floors = [cost(TASK / "authoring" / "variants" / ("ok-" + n))
              for n in policies.FLOOR]

    tmp = Path(tempfile.mkdtemp())
    try:
        rejects = [cost(mutated(sw, tmp / n)) for n, sw in policies.REJECT.items()]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    under = 0

    gt = {"scenarios": {}}
    for sc in scen.SCENARIOS:
        name = sc["name"]
        rep = data["reports"][name]
        want = oracle.replay(sc["ops"])

        if rep["ids"] != {k: list(v) for k, v in want["ids"].items()}:
            print(name, "token sequences do not match the sealed replay")
            return 1
        if rep["spans"] != as_spans(want["spans"]):
            print(name, "trainable spans do not match the sealed replay")
            return 1
        if rep["fwd"] != want["fwd"]:
            print(name, "forward count", rep["fwd"], "against", want["fwd"])
            return 1
        if rep["trace"] != want["trace"]:
            print(name, "lifecycle trace does not match the sealed replay")
            return 1

        low = min(c[name] for c in floors)
        high = max(c[name] for c in ceilings)
        worst = min(c[name] for c in rejects)
        fresh = want["fresh"]

        if fresh > low:
            print(name, "the floor", low, "is under what a private encode pays", fresh)
            return 1
        under += 1 if fresh < low else 0
        if not low <= rep["enc_chars"] <= high:
            print(name, "the reference itself is outside the window",
                  low, rep["enc_chars"], high)
            return 1
        if high >= worst:
            print(name, "the ceiling", high, "admits the answer the task rejects", worst)
            return 1

        gt["scenarios"][name] = {field: rep[field] for field in FIELDS}
        gt["scenarios"][name]["enc_chars"] = rep["enc_chars"]
        gt["scenarios"][name]["enc_chars_min"] = low
        gt["scenarios"][name]["enc_chars_max"] = high
        gt["scenarios"][name]["enc_chars_fresh"] = fresh

        n_pos = sum(b - a for sp in rep["spans"].values() for a, b in sp)
        print("%-14s proved  chars=%-5d window=%d-%d (private encode %d, rejected at %d)"
              "  fwd=%-5d trainable=%d"
              % (name, rep["enc_chars"], low, high, fresh, worst, rep["fwd"], n_pos))

    if not under:
        print("\nno scenario puts the floor above what a private encode pays - the meter "
              "would accept one")
        return 1

    (TASK / "tests" / "gt.json").write_text(json.dumps(gt, indent=1, sort_keys=True) + "\n")
    print("\nthe floor is above a private encode on %d of %d scenarios" % (under, len(gt["scenarios"])))
    print("wrote tests/gt.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
