#!/usr/bin/env python3
"""Time one planner over a whole graded set, the way stage one runs it. Never ships.

Stage one plans every enumerated and every generated pipeline in one process under a 60 second
clock. This does the same in a subprocess with a generous cap, prints the time per family, and
says whether the whole set fits the clock - for the reference, the correct variants, and the
exactly-correct slow cheats alike. `python -u` throughout: buffered output from a timing run
once looked exactly like a hang (CLAUDE.md, reach-pair-sweep).

    python3 -u authoring/restate-hold-plan/timing.py <policy-dir | cheat-name> [cap-seconds]
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

CLOCK = 60

INNER = r'''
import json, sys, time
sys.path.insert(0, %(tests)r)
sys.path.insert(0, %(app)r)
import cases, gen, run_plan
spent = {}
t_all = time.time()
work = [("hand", n, cases.prog(n)) for n in cases.ORDER] + gen.programs("timing", 40)
for fam, name, lines in work:
    t0 = time.time()
    run_plan.run("\n".join(lines) + "\n")
    spent[fam] = spent.get(fam, 0.0) + time.time() - t0
    print(json.dumps({"fam": fam, "t": time.time() - t_all}), flush=True)
print(json.dumps({"done": time.time() - t_all, "spent": spent}), flush=True)
'''


def main():
    what = sys.argv[1]
    cap = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    if Path(what).is_dir():
        here = lab.tree(policy=what)
    else:
        import emit
        emit.OUT.mkdir(exist_ok=True)
        for build in emit.READING_BUILDERS + emit.OTHER_BUILDERS:
            build()
        here = lab.tree(files=emit.BUILT[what])
    script = Path(tempfile.mkdtemp(prefix="rhp-time-")) / "inner.py"
    script.write_text(INNER % {"tests": str(lab.TASK / "tests"), "app": str(here)},
                      encoding="utf-8", newline="\n")
    try:
        done = subprocess.run([sys.executable, "-u", "-B", str(script)], capture_output=True,
                              text=True, timeout=cap)
        out = done.stdout
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        last = [json.loads(l) for l in out.splitlines() if l.startswith("{")]
        print("%s: still running at the %ds cap (%.0fs in, at a %s pipeline) - does not fit %ds"
              % (what, cap, last[-1]["t"] if last else 0, last[-1]["fam"] if last else "?", CLOCK))
        return 0
    rec = [json.loads(l) for l in out.splitlines() if l.startswith("{") and "done" in l]
    if not rec:
        print("%s: failed: %s" % (what, done.stderr[-400:]))
        return 1
    total, spent = rec[-1]["done"], rec[-1]["spent"]
    print("%s: %.1fs for the whole set (%s the %ds clock)"
          % (what, total, "fits" if total < CLOCK else "DOES NOT FIT", CLOCK))
    for fam in sorted(spent, key=spent.get, reverse=True)[:4]:
        print("   %-6s %.1fs" % (fam, spent[fam]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
