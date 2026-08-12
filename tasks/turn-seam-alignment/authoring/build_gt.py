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

The floor is the oracle's own count of what the cheapest legal resume costs: per render,
the last position an encode could have been picked up at and still landed on the sequence
a full encode produces, searched for rather than derived, so no reading of the merge table
can come in under it. A run below the floor has not resumed an encode at all, it has
computed the ids some other way and handed the meter whatever was appended.

The gap between that and the weaker count - the characters that simply were not in the
render before - is the width of that bypass, so it is printed per scenario and the build
refuses to write a ground truth in which no scenario separates the two.

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

import audit  # noqa: E402
import emit  # noqa: E402
import harness  # noqa: E402
import oracle  # noqa: E402
import policies  # noqa: E402
import scen  # noqa: E402

FIELDS = ("enc_calls", "fwd", "trace", "ids", "spans")
PROOFS = {}


def proof(name: str) -> dict:
    if name not in PROOFS:
        PROOFS[name] = oracle.replay(scen.by_name(name)["ops"])
    return PROOFS[name]


def as_spans(raw):
    return {k: [list(x) for x in v] for k, v in raw.items()}


def cost(variant: Path) -> dict:
    """Characters handed to the tokenizer by one implementation, per scenario.

    Taken the way the verifier takes it: worked out again from the tokenizer's own
    record rather than read off the figure the run reported, so the window is calibrated
    against the same quantity it is later graded on.
    """
    data = harness.run(str(variant))
    if data.get("errors"):
        raise SystemExit("%s raised: %s" % (variant.name, sorted(data["errors"])))
    out = {}
    for name, rep in data["reports"].items():
        acct = audit.derive(proof(name), rep)
        if acct["chars"] != rep["enc_chars"]:
            raise SystemExit("%s: %s reported %d characters against %d in the record"
                             % (variant.name, name, rep["enc_chars"], acct["chars"]))
        out[name] = acct["chars"]
    return out


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

    tmp = Path(tempfile.mkdtemp())
    try:
        rejects = [cost(mutated(sw, tmp / n)) for n, sw in policies.REJECT.items()]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    gt = {"scenarios": {}}
    separated = 0
    for sc in scen.SCENARIOS:
        name = sc["name"]
        rep = data["reports"][name]
        want = proof(name)

        try:
            acct = audit.derive(want, rep)
        except audit.Bad as exc:
            print(name, "the reference's own record does not account for its run:", exc)
            return 1
        if acct["chars"] != rep["enc_chars"] or acct["calls"] != rep["enc_calls"]:
            print(name, "the reference's counters disagree with its record",
                  rep["enc_chars"], rep["enc_calls"], acct)
            return 1

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

        low = want["floor"]
        high = max(c[name] for c in ceilings)
        worst = min(c[name] for c in rejects)
        if low > want["fresh"]:
            separated += 1

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

        n_pos = sum(b - a for sp in rep["spans"].values() for a, b in sp)
        print("%-14s proved  chars=%-5d window=%d-%d (appended %d, rejected at %d)"
              "  fwd=%-5d trainable=%d"
              % (name, rep["enc_chars"], low, high, want["fresh"], worst,
                 rep["fwd"], n_pos))

    if not separated:
        print("\nno scenario separates the floor from the characters that were appended, "
              "so a loop that encodes the ids privately and meters only the append is "
              "inside the window")
        return 1

    (TASK / "tests" / "gt.json").write_text(json.dumps(gt, indent=1, sort_keys=True) + "\n")
    print("\nwrote tests/gt.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
