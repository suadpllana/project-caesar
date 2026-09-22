#!/usr/bin/env python3
"""Which layer catches each cheat: the hand cases it fails by name, the nonce launches it fails
by family, and whether it outruns the execution limit. Host emulation - the isolation probes are
skipped here and only mean anything in the two-container run (tools/docker_trial.py).

Only the six collected files are installed, exactly as the worker does, so a cheat that hides
its engine in a seventh file is graded on what is collected (CLAUDE.md, token-seam-emit: a sweep
that never installs the cheat reports clean zeroes).

    python3 -u authoring/stale-line-spin/cheat_report.py [seed] [name-filter]
"""
import collections
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "stale-line-spin"
PARTS = ("line.py", "mem.py", "place.py", "turn.py", "step.py", "clock.py")
LIMIT = 60

RUNNER = r'''
import json, sys, time
sys.path.insert(0, sys.argv[1])      # tests
sys.path.insert(0, sys.argv[2])      # tests/seal
sys.path.insert(0, sys.argv[3])      # app
import cases, gen, model, run_launch
seed, per = sys.argv[4], int(sys.argv[5])
work = [("hand", n, cases.prog(n)) for n in cases.ORDER] + gen.programs(seed, per)
for fam, name, lines in work:
    print(json.dumps({"start": name}), flush=True)
    t0 = time.time()
    try:
        got = run_launch.run("\n".join(lines) + "\n")
    except Exception:
        got = None
    dt = time.time() - t0
    print(json.dumps({"fam": fam, "name": name, "ok": got == model.expect(lines),
                      "dt": round(dt, 2)}), flush=True)
print(json.dumps({"done": True}), flush=True)
'''


def files_of(script):
    text = script.read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"cat > /app/sim/(\w+\.py) <<'PYEOF'\n(.*?)\nPYEOF", text, re.S):
        out[m.group(1)] = m.group(2) + "\n"
    return out


def trial(files, seed, per):
    """Stream one record per launch, so a run that stalls still says what it failed first."""
    room = pathlib.Path(tempfile.mkdtemp(prefix="sls-cheat-"))
    try:
        app = room / "app"
        shutil.copytree(TASK / "environment" / "app_src", app)
        for part in PARTS:
            if part in files:
                (app / "sim" / part).write_text(files[part], encoding="utf-8")
        runner = room / "runner.py"
        runner.write_text(RUNNER, encoding="utf-8")
        out = room / "out.jsonl"
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        with open(out, "w") as fh:
            p = subprocess.Popen([sys.executable, "-u", str(runner), str(TASK / "tests"),
                                  str(TASK / "tests" / "seal"), str(app), seed, str(per)],
                                 stdout=fh, stderr=subprocess.PIPE, text=True, env=env)
            try:
                _, err = p.communicate(timeout=LIMIT * 4)
                stalled = False
            except subprocess.TimeoutExpired:
                p.kill()
                _, err = p.communicate()
                stalled = True
        recs = [json.loads(x) for x in out.read_text().splitlines() if x.strip()]
        res = {"hand": [], "nonce": {}, "ran": 0, "stalled": stalled, "crash": None,
               "slowest": None, "at": None}
        done = False
        for r in recs:
            if r.get("done"):
                done = True
                continue
            if "start" in r:
                res["at"] = r["start"]
                continue
            res["ran"] += 1
            if res["slowest"] is None or r["dt"] > res["slowest"][1]:
                res["slowest"] = (r["name"], r["dt"])
            if not r["ok"]:
                if r["fam"] == "hand":
                    res["hand"].append(r["name"])
                else:
                    res["nonce"][r["fam"]] = res["nonce"].get(r["fam"], 0) + 1
        if not done and not stalled:
            res["crash"] = (err or "")[-300:]
        return res
    finally:
        shutil.rmtree(room, ignore_errors=True)


def timed(files, seed, per):
    """Run the worker's own loop under the real limit, to see whether a cheat is slow."""
    room = pathlib.Path(tempfile.mkdtemp(prefix="sls-slow-"))
    try:
        work = room / "work"
        work.mkdir()
        (work / "nonce").write_text(seed + "\n")
        (work / "per").write_text("%d\n" % per)
        sub = room / "sub"
        sub.mkdir()
        for part in PARTS:
            if part in files:
                (sub / part).write_text(files[part], encoding="utf-8")
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", SLS_TESTS=str(TASK / "tests"),
                   SLS_WORK=str(work), SLS_SUB=str(sub))
        try:
            subprocess.run([sys.executable, str(TASK / "tests" / "worker.py"), "--out",
                            str(work / "o.json")], env=env, timeout=LIMIT, capture_output=True)
            return False
        except subprocess.TimeoutExpired:
            return True
    finally:
        shutil.rmtree(room, ignore_errors=True)


def main():
    seed = sys.argv[1] if len(sys.argv) > 1 else "report"
    flt = sys.argv[2] if len(sys.argv) > 2 else ""
    per = 40
    graded, missed = 0, []
    for script in sorted((TASK / "cheat").glob("cheat-*.sh")):
        name = script.name[len("cheat-"):-3]
        if flt and flt not in name:
            continue
        if name.startswith("probe-") and name != "probe-uncollected-file":
            print("%-24s (isolation probe: container only)" % name, flush=True)
            continue
        files = files_of(script)
        r = trial(files, seed, per)
        graded += 1
        fams = ", ".join("%s %d" % kv for kv in sorted(r["nonce"].items()))
        if r["crash"] is not None:
            last = [x for x in r["crash"].strip().splitlines() if x.strip()][-1:] or ["?"]
            print("%-24s %-10s runner died after %d launches: %s" % (
                name, "CAUGHT", r["ran"], last[0]), flush=True)
            continue
        slow = ""
        if r["stalled"]:
            slow = " | stalled in %s after %d launches over %ds" % (r["at"], r["ran"], LIMIT * 4)
        elif not r["hand"] and not r["nonce"] and timed(files, seed, per):
            slow = " | over the %ds limit" % LIMIT
        verdict = "CAUGHT" if (r["hand"] or r["nonce"] or slow) else "NOT CAUGHT"
        if verdict != "CAUGHT":
            missed.append(name)
        print("%-24s %-10s hand %2d %s | nonce %s%s" % (
            name, verdict, len(r["hand"]), r["hand"][:4], fams or "-", slow), flush=True)
    if missed:
        print("%d of %d cheats graded here NOT CAUGHT: %s" % (len(missed), graded, ", ".join(missed)))
        return 1
    print("all %d cheats graded here caught (isolation probes: container only)" % graded)
    return 0


if __name__ == "__main__":
    sys.exit(main())
