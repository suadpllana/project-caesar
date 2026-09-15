"""Run a shipped script under the reference, the model and (optionally) the shipped tree."""
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TASK = ROOT / "tasks" / "blend-roll-resume"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import lab  # noqa: E402
import model  # noqa: E402

REF = TASK / "solution"


def main():
    path = TASK / "environment" / "app_src" / "progs" / sys.argv[1]
    lines = [x.strip() for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    t = time.perf_counter()
    ref = lab.inproc(lines, REF)
    dt = time.perf_counter() - t
    want = model.expect(lines)
    print("-- reference (%.3fs) --" % dt)
    for line in ref:
        print("  ", line)
    print("model agrees:", ref == want)
    if "--ship" in sys.argv:
        t = time.perf_counter()
        ship = lab.run(lines, None, timeout=int(sys.argv[sys.argv.index("--ship") + 1])
                       if len(sys.argv) > sys.argv.index("--ship") + 1 else 120)
        print("-- shipped (%.3fs) --" % (time.perf_counter() - t))
        for line in (ship.get("out") or []):
            print("  ", line)
        if ship.get("err"):
            print("   err:", ship["err"])
        if ship.get("out") is not None:
            same = [a == b for a, b in zip(ship["out"], ref)]
            print("   lines differing:", [i for i, ok in enumerate(same) if not ok],
                  "len", len(ship["out"]), len(ref))


if __name__ == "__main__":
    main()
