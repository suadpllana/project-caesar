"""Time the graded set itself: the worker, over every plan, under one policy.

This is the number the 60-second limit is set against, so it is measured rather than assumed.

    python3 time_worker.py                 the reference
    python3 time_worker.py slow/fold       any policy directory
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

import lab

HERE = pathlib.Path(__file__).resolve().parent
PER = 45


def main(argv):
    policy = lab.reference() if not argv else (HERE / argv[0])
    room = pathlib.Path(tempfile.mkdtemp(prefix="mrr-time-"))
    work = room / "work"
    work.mkdir()
    app = room / "app"
    shutil.copytree(lab.APP, app)
    for part in lab.PARTS:
        one = pathlib.Path(policy) / part
        if one.is_file():
            shutil.copy(one, app / "feed" / part)
    (work / "nonce").write_text("timing-nonce", encoding="utf-8")
    (work / "per").write_text("%d\n" % PER, encoding="utf-8")
    env = {"MRR_TESTS": str(lab.TASK / "tests"), "MRR_WORK": str(work),
           "MRR_SUB": str(app / "feed"), "PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"}
    t0 = time.time()
    proc = subprocess.run([sys.executable, str(lab.TASK / "tests" / "worker.py"),
                           "--out", str(work / "out.json")],
                          capture_output=True, text=True, env=env, timeout=3600)
    took = time.time() - t0
    if proc.returncode != 0:
        print(proc.stderr[-2000:])
        return 1
    recs = json.loads((work / "out.json").read_text(encoding="utf-8"))
    fams = {}
    for r in recs:
        fams[r["fam"]] = fams.get(r["fam"], 0) + 1
    print("%s: %d plans in %.2f s (%s)"
          % (argv[0] if argv else "reference", len(recs), took,
             ", ".join("%s %d" % (k, v) for k, v in sorted(fams.items()))))
    raised = [r["name"] for r in recs if r["got"] is None]
    print("   raised: %d %s" % (len(raised), raised[:4]))
    shutil.rmtree(room, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
