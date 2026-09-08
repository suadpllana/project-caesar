"""Build the graded scripts as root, before any agent code runs.

The worker executes the submitted accounting layer, so anything the worker can read, the
submission can read. The scripts are input and may be handed over; the model, the ground truth
and the generator that knows how to reproduce either are answers, and they stay root-only. That
is why generation happens here rather than inside the worker: after this stage the sandbox uid
needs nothing from /tests but the runner and the pristine store.
"""
import json
import os
import pathlib
import sys

TESTS = os.environ.get("SCS_TESTS", "/tests")
sys.path.insert(0, TESTS)

import cases  # noqa: E402
import gen  # noqa: E402

LOGS = pathlib.Path(os.environ.get("SCS_LOGS", "/logs/verifier"))


def scripts():
    out = [{"fam": "hand", "name": nm, "lines": list(cases.CASES[nm])} for nm in cases.ORDER]
    out += [{"fam": "shipped", "name": "runs-" + nm, "lines": cases.shipped(nm)}
            for nm in cases.SHIPPED]
    seed = (LOGS / "nonce").read_text(encoding="utf-8").strip()
    per = int((LOGS / "per").read_text(encoding="utf-8").strip())
    for fam, name, lines in gen.programs(seed, per):
        out.append({"fam": fam, "name": name, "lines": list(lines)})
    return out


def main():
    out = sys.argv[sys.argv.index("--out") + 1]
    pathlib.Path(out).write_text(json.dumps(scripts()), encoding="utf-8")
    print("prepared %d scripts" % len(scripts()))


if __name__ == "__main__":
    main()
