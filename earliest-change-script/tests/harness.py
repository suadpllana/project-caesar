"""Parent process. Never imports the submitted module.

Everything that has to be true independently of the submitted code is decided
here: how long a child took, and whether it finished at all. Each large case is
its own child under its own budget, so a run that never returns is killed
rather than believed, and one slow case cannot spend another case's time.

The report goes to standard output, which the verifier has already pointed at a
file this account cannot create, replace or unlink.
"""

import json
import os
import subprocess
import sys
import time

sys.path.insert(0, "/tmp/sbx")

import casegen  # noqa: E402

RUNNER = "/tmp/sbx/runner.py"
CASES_BUDGET = 900.0
SEED = int(os.environ.get("RUN_SEED", "0"))
N_RANDOM = 12000


def child(cases, budget):
    payload = json.dumps({"cases": cases}).encode()
    started = time.monotonic()
    try:
        done = subprocess.run([sys.executable, RUNNER], input=payload,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=budget)
    except subprocess.TimeoutExpired:
        return {"error": "no answer within %.1f seconds" % budget}, \
            round(time.monotonic() - started, 3)
    elapsed = round(time.monotonic() - started, 3)
    try:
        return json.loads(done.stdout.decode() or "{}"), elapsed
    except Exception as exc:
        return {"error": "unreadable output: %s" % exc}, elapsed


def main():
    report = {"seed": SEED}

    cases = list(casegen.FIXED) + casegen.random_cases(N_RANDOM, SEED) \
        + casegen.structured_cases()
    got, secs = child(cases, CASES_BUDGET)
    report["cases"] = got
    report["cases_seconds"] = secs

    got, secs = child(casegen.medium_cases(SEED), casegen.MEDIUM_BUDGET)
    report["medium"] = got
    report["medium_seconds"] = secs

    timed = []
    for index in range(len(casegen.TIMED_SHAPES)):
        before, after = casegen.timed_case(index, SEED)
        got, secs = child([[before, after]], casegen.TIMED_BUDGET)
        entry = {"seconds": secs}
        if "error" in got:
            entry["error"] = got["error"]
        else:
            answers = got.get("answers") or [None]
            entry["answer"] = answers[0]
        if got.get("tamper"):
            entry["tamper"] = got["tamper"]
        timed.append(entry)
    report["timed"] = timed

    sys.stdout.write(json.dumps(report))


if __name__ == "__main__":
    main()
