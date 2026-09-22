#!/usr/bin/env python3
"""Three implementations, one contract: the reference, the sealed model, and a naive engine.

`proto/naive.py` is written the way the brief reads literally - the work list re-derived
whenever anything moves - so it shares no structure with either of the two that ship. Running
all three over the same random programs is what the claim of independence in
`tests/seal/model.py` rests on.

    python3 -u authoring/pin-drift-redo/diff.py [rounds]
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "proto"))
import lab  # noqa: E402
import mkprog  # noqa: E402
import naive  # noqa: E402

cases, gen, model = lab.sealed()


def main(rounds):
    here = lab.tree(lab.TASK / "solution")
    bad = 0
    for seed in range(rounds):
        text = mkprog.prog(seed, keys=3 + seed % 6, ops=15 + seed % 80)
        want = model.expect(text.splitlines())
        got = lab.run_text(here, text)
        other = naive.run(text)
        if got != want or other != want:
            bad += 1
            if bad == 1:
                print("DIFF at seed %d\n%s\nreference %s\nmodel     %s\nnaive     %s"
                      % (seed, text, got, want, other))
    print("%d random programs, %d disagreements" % (rounds, bad), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 5000))
