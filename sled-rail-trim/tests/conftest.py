"""Session bookkeeping.

Writes a verdict carrying this run's nonce. test.sh refuses to hand out a
reward on an exit code alone, so this file is what says the session really
finished and really passed.
"""

import json
import os

import pytest


def pytest_configure(config):
    config._verify_counts = {"passed": 0, "failed": 0, "error": 0, "skipped": 0}


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    counts = item.config._verify_counts
    if report.when == "call":
        if report.passed:
            counts["passed"] += 1
        elif report.failed:
            counts["failed"] += 1
    elif report.when in ("setup", "teardown") and report.failed:
        counts["error"] += 1


def pytest_sessionfinish(session, exitstatus):
    path = os.environ.get("CHECK_VERDICT")
    if not path:
        return
    counts = session.config._verify_counts
    verdict = {
        "nonce": os.environ.get("CHECK_NONCE", ""),
        "seed": os.environ.get("CHECK_SEED", ""),
        "exitstatus": int(exitstatus),
        "passed": bool(
            int(exitstatus) == 0
            and counts["failed"] == 0
            and counts["error"] == 0
            and counts["passed"] > 0
        ),
        "counts": counts,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(verdict, fh)
