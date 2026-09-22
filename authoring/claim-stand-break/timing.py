"""Time the reference and the correct-but-naive readings over the whole graded set."""
import json
import pathlib
import subprocess
import sys
import time

import lab

TESTS = lab.ROOT / "tasks" / "claim-stand-break" / "tests"
sys.path.insert(0, str(TESTS))
import gen  # noqa: E402

RUN = '''
import json, sys, time
sys.path.insert(0, sys.argv[1])
sys.path.insert(0, sys.argv[2])
import run_tx, gen
work = [("hand", n, l) for n, l in []]
work += gen.programs(sys.argv[4], int(sys.argv[5]))
best = {}
t0 = time.time()
for fam, name, lines in work:
    a = time.time()
    run_tx.run("\\n".join(lines) + "\\n")
    best[fam] = best.get(fam, 0.0) + time.time() - a
json.dump({"total": time.time() - t0, "fam": best}, open(sys.argv[3], "w"))
'''


def timed(where, tag, seed="t1", per=40, seconds=1800):
    room = lab.tree(where)
    (room / "_run.py").write_text(RUN, encoding="utf-8")
    out = room / "t.json"
    t0 = time.time()
    proc = subprocess.run([sys.executable, "-u", str(room / "_run.py"), str(room), str(TESTS),
                           str(out), seed, str(per)], capture_output=True, text=True,
                          timeout=seconds)
    if proc.returncode != 0:
        print("%-12s FAILED %s" % (tag, proc.stderr[-800:]))
        return None
    got = json.loads(out.read_text())
    print("%-12s total %7.2fs   deep %6.2f  wide %6.2f  rest %6.2f" % (
        tag, got["total"], got["fam"].get("deep", 0), got["fam"].get("wide", 0),
        got["total"] - got["fam"].get("deep", 0) - got["fam"].get("wide", 0)))
    return got


if __name__ == "__main__":
    which = sys.argv[1:] or ["ok", "walk", "answer", "ship"]
    where = {
        "ok": lab.ROOT / "tasks" / "claim-stand-break" / "solution",
        "walk": pathlib.Path("variants/slow-walk"),
        "answer": pathlib.Path("variants/slow-answer"),
        "ship": None,
    }
    for tag in which:
        base = lab.tree(where["ok"]) if tag in ("walk", "answer") else None
        if tag in ("walk", "answer"):
            room = where[tag]
            import shutil
            for one in (lab.ROOT / "tasks" / "claim-stand-break" / "solution").glob("*.py"):
                if not (room / one.name).is_file():
                    shutil.copy(one, room / one.name)
        timed(where[tag], tag)
