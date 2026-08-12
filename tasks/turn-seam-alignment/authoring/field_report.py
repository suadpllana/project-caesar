#!/usr/bin/env python3
"""Per-variant, which graded field diverges from the ground truth.

A graded field that separates no wrong answer is pure liability: it cannot catch a
mistake and it can still fail a correct solution. This prints the failure signature of
every script in cheat/ (and of any directory of editable files passed on the command
line), field by field, so the graded set can be checked against what it actually does.

`enc_chars` is compared the way the verifier compares it, against the window rather than
against the reference's own number, so a variant that resumes from different positions
for a good reason shows up here as clean.

Usage:
    python3 authoring/field_report.py
    python3 authoring/field_report.py authoring/variants/ok-pair
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "authoring"))
sys.path.insert(0, str(TASK / "tests"))

import audit  # noqa: E402
import harness  # noqa: E402
import oracle  # noqa: E402
import scen  # noqa: E402

# enc_record is the tokenizer's own account of the run, replayed against the sealed
# encoder the way tests/audit.py does it at verification time; enc_chars and enc_calls
# are then the figures that replay derives, not the ones the run reported.
GRADED = ("ids", "spans", "enc_record", "enc_chars", "enc_calls", "fwd", "trace")
NAMES = [s["name"] for s in scen.SCENARIOS]
PROOFS = {}


def proof(name: str) -> dict:
    if name not in PROOFS:
        PROOFS[name] = oracle.replay(scen.by_name(name)["ops"])
    return PROOFS[name]


def gt():
    return json.loads((TASK / "tests" / "gt.json").read_text())["scenarios"]


def from_script(path: Path, dest: Path) -> None:
    """Replay a cheat script's heredocs into a directory of editable files."""
    text = path.read_text()
    dest.mkdir(parents=True, exist_ok=True)
    for m in re.finditer(r"cat > /app/\S*?/?(\w+\.py) <<'PYEOF'\n(.*?)\nPYEOF", text, re.S):
        (dest / m.group(1)).write_text(m.group(2) + "\n")


def diverged(field, got, want):
    if field == "enc_chars":
        if not isinstance(got, int) or isinstance(got, bool):
            return True
        return not want["enc_chars_min"] <= got <= want["enc_chars_max"]
    return got != want[field]


def signature(variant: str) -> dict:
    data = harness.run(str(Path(variant).resolve()))
    want = gt()
    out = {}
    for name in NAMES:
        rep = (data.get("reports") or {}).get(name)
        if not isinstance(rep, dict):
            out[name] = ["RAISED"]
            continue
        try:
            got = audit.derive(proof(name), rep)
        except audit.Bad:
            got = None
        # The grader takes the derived figures and requires the reported ones to match,
        # so a record that does not account for the run, and a disagreement between the
        # two, both land on the fields below rather than on whatever the run said.
        seen = dict(rep)
        hits = []
        if got is None:
            hits.append("enc_record")
            seen["enc_chars"] = None
            seen["enc_calls"] = None
        else:
            for field, value in (("enc_chars", got["chars"]), ("enc_calls", got["calls"])):
                seen[field] = value if rep.get(field) == value else None
        out[name] = hits + [f for f in GRADED if f != "enc_record"
                            and diverged(f, seen.get(f), want[name])]
    return out


def show(label: str, sig: dict) -> None:
    hit = {f for v in sig.values() for f in v}
    print("%-32s %s" % (label, ("clean" if not hit else " ".join(sorted(hit)))))
    for name in NAMES:
        if sig[name]:
            print("      %-13s %s" % (name, " ".join(sig[name])))


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        for v in argv[1:]:
            show(v, signature(v))
        return 0

    tmp = Path(tempfile.mkdtemp())
    seen = {}
    for sh in sorted((TASK / "cheat").glob("cheat-*.sh")):
        if "reward-daemon" in sh.name or "plant-run-output" in sh.name:
            continue  # these tamper with the verifier rather than answer it
        d = tmp / sh.stem
        from_script(sh, d)
        if not any(d.glob("*.py")):
            continue
        sig = signature(str(d))
        seen[sh.stem] = sig
        show(sh.stem, sig)

    print()
    separates = {f: sorted(k for k, sig in seen.items()
                           if any(f in v for v in sig.values()))
                 for f in GRADED}
    dead = []
    for field in GRADED:
        print("%-12s separates %s" % (field, ", ".join(separates[field]) or "NOTHING"))
        if not separates[field]:
            dead.append(field)
    if dead:
        print("\ndead weight in the graded set: %s" % ", ".join(dead))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
