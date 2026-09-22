"""Freeze tests/seal/gt.json from the sealed model, after the three implementations agree.

gt.json holds the answer to every enumerated program. The grader asserts that the model still
reproduces it before judging anything, so the file is only ever written from the model, and only
when the brute-force transcription and the reference agree with the model on every program.

The easiness recovery of 2026-09-22 changed the contract (borrowed heights, the memory, the hold
restriction, the clamp after an edit), so no answer frozen before it can survive; this script
reports how many of the old answers moved rather than asserting they did not.

    python3 authoring/row-anchor-pass/build_gt.py
"""
import json
import sys

import brute
import lab

cases, _gen, model = lab.sealed()
GT = lab.TASK / "tests" / "seal" / "gt.json"


def main():
    old = {}
    if GT.is_file():
        old = json.loads(GT.read_text(encoding="utf-8"))
    run = lab.pane("solution")
    out = {}
    bad = []
    for name in cases.ORDER:
        lines = cases.prog(name)
        want = model.expect(lines)
        if brute.expect(lines) != want or run(lines) != want:
            bad.append(name)
        out[name] = want
    if bad:
        print("REFUSED: the implementations disagree on %s" % bad)
        return 1
    moved = sum(1 for k in out if k in old and old[k] != out[k])
    kept = sum(1 for k in out if k in old and old[k] == out[k])
    text = json.dumps(out, indent=1, sort_keys=True) + "\n"
    assert "\r" not in text
    GT.write_text(text, encoding="utf-8", newline="\n")
    print("wrote %d answers (%d new, %d moved, %d unchanged from the previous file)"
          % (len(out), len([k for k in out if k not in old]), moved, kept))
    return 0


if __name__ == "__main__":
    sys.exit(main())
