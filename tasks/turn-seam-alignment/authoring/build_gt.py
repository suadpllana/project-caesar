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

The two counters the oracle deliberately does not model - characters handed to the
tokenizer and calls made to it - come from the reference alone. Those are the accounting
the task is about, and there is no cheaper implementation of them than an implementation
that is right.

Usage:  python3 authoring/build_gt.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "authoring"))
sys.path.insert(0, str(TASK / "tests"))

import harness  # noqa: E402
import oracle  # noqa: E402
import scen  # noqa: E402

FIELDS = ("enc_chars", "enc_calls", "fwd", "trace", "ids", "spans")


def as_spans(raw):
    return {k: [list(x) for x in v] for k, v in raw.items()}


def main() -> int:
    data = harness.run("solution/ref")
    if data.get("errors"):
        for name, err in data["errors"].items():
            print("reference failed on", name, "\n", err)
        return 1

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

        gt["scenarios"][name] = {field: rep[field] for field in FIELDS}
        n_pos = sum(b - a for sp in rep["spans"].values() for a, b in sp)
        print("%-14s proved  chars=%-5d fwd=%-5d trainable=%d"
              % (name, rep["enc_chars"], rep["fwd"], n_pos))

    (TASK / "tests" / "gt.json").write_text(json.dumps(gt, indent=1, sort_keys=True) + "\n")
    print("\nwrote tests/gt.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
