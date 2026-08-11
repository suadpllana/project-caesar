"""Parent process. Never imports the submitted module.

Everything worth measuring is measured out here: the wall clock wrapped round
a child, and whether that child came back at all. The timed workload gets its
own process with a limit enforced from outside it, so a planner that never
returns is killed rather than waited on.

The report goes to stdout, which the verifier has already pointed at a file
created by root in a directory this account cannot write into.
"""

import json
import os
import subprocess
import sys
import time

sys.path.insert(0, "/tmp/sbx")

import casegen  # noqa: E402

RUNNER = "/tmp/sbx/runner.py"
CASE_LIMIT = 600


def run_child(job, limit):
    started = time.monotonic()
    try:
        proc = subprocess.run(
            [sys.executable, RUNNER],
            input=json.dumps(job).encode(),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=limit)
    except subprocess.TimeoutExpired:
        return None, round(time.monotonic() - started, 3), "timeout"
    elapsed = round(time.monotonic() - started, 3)
    try:
        return json.loads(proc.stdout.decode() or "{}"), elapsed, None
    except Exception as exc:
        tail = proc.stderr.decode()[-400:]
        return None, elapsed, "unreadable output: %s (stderr: %s)" % (exc, tail)


def main():
    seed = int(os.environ["RUN_SEED"])
    report = {"seed": seed}

    # Two blocks, two manifests, each its own child. The small one is graded
    # by trying every assignment; the wide one is too big for that.
    blocks = [(casegen.small_manifest(), casegen.small_filters()),
              (casegen.wide_manifest(), casegen.wide_filters())]
    plain, held, tamper = [], [], []
    elapsed = 0.0
    for manifest, filters in blocks:
        got, secs, err = run_child(
            {"mode": "cases", "manifest": manifest, "filters": filters},
            CASE_LIMIT)
        elapsed += secs
        if err or got is None:
            report["error"] = err or "no output"
            break
        tamper.extend(got.get("tamper") or [])
        if "error" in got:
            report["error"] = got["error"]
            break
        if not isinstance(got.get("plain"), list) or not isinstance(
                got.get("held"), list):
            report["error"] = "the reader returned no usable answers"
            break
        plain.extend(got["plain"])
        held.extend(got["held"])
    report["case_seconds"] = round(elapsed, 3)
    report["plain"] = plain
    report["held"] = held
    report["tamper"] = tamper

    # Room well past the budget on purpose: a reader that is right and slow
    # should still be graded right and fail only the clock, so the child is
    # killed only when it has stopped being evidence of anything.
    got, secs, err = run_child({"mode": "timed", "seed": seed},
                               casegen.TIMED_BUDGET * 5)
    timed = {"seconds": secs, "error": err}
    if got:
        timed.update({k: got.get(k) for k in ("digest", "queries", "files")})
        if got.get("error"):
            timed["error"] = got["error"]
        report["tamper"] = (report.get("tamper") or []) + (got.get("tamper") or [])
    report["timed"] = timed

    sys.stdout.write(json.dumps(report))


if __name__ == "__main__":
    main()
