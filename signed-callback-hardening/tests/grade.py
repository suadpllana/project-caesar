"""Decide the reward from evidence, not from an exit status.

Run by tests/test.sh as root, in a fresh process that imports nothing from /app and
therefore never touches agent-supplied code. A run counts as a pass only when pytest
exited cleanly AND the CTRF report shows every expected test actually executed and
passed. A truncated run, a killed runner, a report that is missing, stale, unparseable
or short one test all grade as 0.

Usage: grade.py <ctrf.json> <expected_tests.txt> <pytest-exit-status> <not-before-ms>
"""

import json
import sys
from pathlib import Path

PASSING = "passed"


def fail(reason):
    print("grade: FAIL - " + reason)
    return 1


def main(argv):
    if len(argv) != 5:
        print(__doc__)
        return 2

    report_path, expected_path, status_text, floor_text = argv[1:]
    try:
        status = int(status_text)
        floor_ms = int(floor_text)
    except ValueError:
        return fail("bad arguments")

    if status != 0:
        return fail("pytest exited with status %d" % status)

    expected = {line.strip() for line in Path(expected_path).read_text().splitlines() if line.strip()}
    if not expected:
        return fail("the expected-test list is empty, so nothing could be verified")

    report_file = Path(report_path)
    if not report_file.is_file():
        return fail("no CTRF report at %s" % report_path)
    try:
        report = json.loads(report_file.read_text())
    except ValueError as exc:
        return fail("the CTRF report is not valid JSON (%s)" % exc)

    results = report.get("results")
    if not isinstance(results, dict):
        return fail("the CTRF report has no results section")

    summary = results.get("summary") or {}
    cases = results.get("tests") or []
    if not isinstance(cases, list) or not cases:
        return fail("the CTRF report lists no executed tests")

    # The report must belong to this run, not to a file planted before it started.
    started = summary.get("start")
    if not isinstance(started, int) or started < floor_ms:
        return fail("the CTRF report predates this run (start=%r, floor=%d)" % (started, floor_ms))

    for field in ("failed", "skipped", "pending", "other"):
        count = summary.get(field)
        if count != 0:
            return fail("the run reported %r %s" % (count, field))

    executed = {}
    for case in cases:
        if not isinstance(case, dict):
            return fail("the CTRF report contains a malformed test entry")
        executed[str(case.get("name"))] = str(case.get("status"))

    missing = sorted(expected - set(executed))
    if missing:
        return fail("%d expected test(s) never ran: %s" % (len(missing), ", ".join(missing)))

    unexpected = sorted(set(executed) - expected)
    if unexpected:
        return fail("the report contains tests that are not part of the suite: %s"
                    % ", ".join(unexpected))

    not_passed = sorted(name for name, state in executed.items() if state != PASSING)
    if not_passed:
        return fail("%d test(s) did not pass: %s" % (len(not_passed), ", ".join(not_passed)))

    if summary.get("tests") != len(expected) or summary.get("passed") != len(expected):
        return fail("the summary counts (%r tests, %r passed) disagree with the %d expected tests"
                    % (summary.get("tests"), summary.get("passed"), len(expected)))

    print("grade: PASS - %d of %d tests executed and passed" % (len(executed), len(expected)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
