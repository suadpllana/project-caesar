"""Which kind of trace row separates each cheat, so no graded row kind is dead weight.

A row kind that separates no cheat cannot catch a wrong answer and can still fail a right one.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

import stage
import trial

KINDS = ["tk", "ch", "dp", "br", "fi", "rw", "en"]


def rows_for(script, count):
    work = tempfile.mkdtemp(prefix="ahc-field-")
    try:
        app, tests, _ = trial.lay(work, None if script else
                                  [os.path.join(stage.SOLUTION, n) for n in ("hold.py", "pick.py")])
        if script:
            trial.play(app, script)
        report = os.path.join(work, "out.json")
        env = dict(os.environ, APPDIR=app, RUN_NONCE="field", RUN_COUNT=str(count),
                   PYTHONPATH=os.pathsep.join([app, tests]), PYTHONDONTWRITEBYTECODE="1")
        subprocess.run([sys.executable, os.path.join(tests, "runner.py"), report],
                       env=env, capture_output=True, text=True, cwd=work)
        if not os.path.exists(report):
            return None
        return json.load(open(report))["runs"]
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    base = rows_for(None, count)
    seen = {k: 0 for k in KINDS}
    for name in sorted(os.listdir(trial.CHEATS)):
        if not name.endswith(".sh"):
            continue
        got = rows_for(os.path.join(trial.CHEATS, name), count)
        if got is None:
            print("%-24s no report" % name[6:-3])
            continue
        kinds = set()
        for job, want in base.items():
            mine = got.get(job)
            if mine == want:
                continue
            for a, b in zip(want, mine or []):
                if a != b:
                    kinds.add(a[0] if isinstance(a, list) else "?")
                    kinds.add(b[0] if isinstance(b, list) else "?")
                    break
            if len(want) != len(mine or []):
                longer = want if len(want) > len(mine or []) else mine
                kinds.add(longer[min(len(want), len(mine or []))][0])
        for k in kinds:
            if k in seen:
                seen[k] += 1
        print("%-24s separated by %s" % (name[6:-3], sorted(kinds)))
    dead = [k for k, n in seen.items() if n == 0]
    print("row kinds separating nothing: %s" % (dead or "none"))
    return 1 if dead else 0


if __name__ == "__main__":
    raise SystemExit(main())
