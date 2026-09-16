"""Run every correct variant over the enumerated and generated populations.

A variant that follows the contract but is built differently must score exactly
what the reference scores. One that comes out wrong is a verifier grading an
implementation choice, not the contract.

    python variant_check.py [nonce] [per]
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import harness  # noqa: E402

VARIANTS = os.path.join(HERE, "variants")


def main():
    nonce = sys.argv[1] if len(sys.argv) > 1 else "variantprobe"
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    want = harness.model_traces(nonce, per)
    rows = []
    for name in sorted(os.listdir(VARIANTS)):
        d = os.path.join(VARIANTS, name)
        if not os.path.isdir(d):
            continue
        got = harness.traces(d, nonce, per)
        bad = [k for k in want if got.get(k) != want[k]]
        rows.append((name, len(bad)))
        print("%-10s %d plans, %d disagreements" % (name, len(want), len(bad)))
        for k in bad[:2]:
            a, b = got.get(k, []), want[k]
            for i in range(max(len(a), len(b))):
                x = a[i] if i < len(a) else "<missing>"
                y = b[i] if i < len(b) else "<extra>"
                if x != y:
                    print("   %s line %d: %r want %r" % (k, i + 1, x, y))
                    break
    bad = [n for n, c in rows if c]
    print("\n%d/%d variants match the model" % (len(rows) - len(bad), len(rows)))
    return 1 if bad else 0


sys.exit(main())
