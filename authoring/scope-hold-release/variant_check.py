"""Compare the reference and four structurally different correct policies."""

from __future__ import annotations

import sys
from pathlib import Path

import harness


def main(argv):
    rounds = int(argv[1]) if len(argv) > 1 else 600
    rows = [("reference", harness.TASK / "solution")]
    rows.extend(
        (p.name, p)
        for p in sorted((Path(__file__).parent / "variants").iterdir())
        if p.is_dir() and p.name.startswith("ok-")
    )
    failed = 0
    for name, policy in rows:
        result = harness.check(policy, rounds)
        ok = not result["fixed"] and result["generated"] == 0
        failed += not ok
        print("%-24s %s" % (name, "agrees" if ok else "DISAGREES %r" % result))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
