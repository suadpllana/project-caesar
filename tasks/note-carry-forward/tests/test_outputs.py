"""The grader. Runs as root, after the sandboxed run has finished and been
reaped, and never imports anything the submission could have written.

The contract, frozen before the environment was written:

  graded          the thread table at the head of every stream - id, state
                  and span for each - and the ordered log of what happened to
                  the threads on the way
  not graded      anything about how the board stores its state, what it
                  computes first, or how many times it walks the store
  ground truth    tests/gt.json, root-only, rebuilt by authoring/build_gt.py
                  and re-proved at grading time by tests/oracle.py, which
                  shares no code with the environment or the reference

Event order inside one revision is part of the contract and is stated in the
brief, because two correct boards would otherwise disagree about the log for
no reason anybody could grade: everything the carry retired, then everything
it raised, then the absorbing, each in ascending note order.
"""

import json
import os
import pathlib

import pytest

import oracle
import scen

WORK = pathlib.Path("/work")
TRUTH = pathlib.Path("/tests/gt.json")


def _report():
    """The run writes its report in one go at the end, so a run that was killed
    for taking too long leaves this empty. That is a verdict about the
    submission rather than a fault in the harness, so it is read as an empty
    set of boards and the tests below say which streams never came back. A
    fixture that raises instead reports five errors and no reason."""
    try:
        raw = (WORK / "out.json").read_text()
    except OSError:
        return {"boards": {}}
    try:
        got = json.loads(raw)
    except ValueError:
        return {"boards": {}}
    if not isinstance(got, dict):
        return {"boards": {}}
    got.setdefault("boards", {})
    return got


@pytest.fixture(scope="module")
def report():
    return _report()


@pytest.fixture(scope="module")
def truth():
    return json.loads(TRUTH.read_text())


def _count(name, fallback):
    return int(os.environ.get(name, fallback))


def test_the_board_ran_at_all(report):
    assert report.get("boards"), "the run produced no boards"


def test_the_fixed_streams_match_the_rule(report, truth):
    boards = report["boards"]
    wrong = []
    for item in scen.FIXED:
        name = item["name"]
        got = boards.get(name)
        want = truth["fixed"][name]
        if got != want:
            wrong.append(name)
    assert not wrong, "wrong on %d of %d hand-written streams: %s" % (
        len(wrong), len(scen.FIXED), ", ".join(wrong[:8]))


def test_the_generated_streams_match_the_rule(report):
    """Built from the seed this run was given, which is chosen after the
    submission was written, and settled here by the sealed model."""
    seed = report.get("seed")
    assert isinstance(seed, int), "the report carries no seed; the run did not finish"
    boards = report["boards"]
    wrong = []
    for item in scen.generated(_count("RUN_COUNT", "300"), seed):
        threads, log = oracle.board(item["revs"], item["events"])
        want = {"threads": threads, "log": log}
        if boards.get(item["name"]) != want:
            wrong.append(item["name"])
    assert not wrong, "wrong on %d generated streams, first: %s" % (
        len(wrong), ", ".join(wrong[:8]))


def test_the_wide_streams_match_the_rule(report):
    """The streams that carry a few hundred threads at once. A board that
    settles which lines a change reaches once for each thread on the board,
    rather than once for the pair of revisions, does not finish these inside
    the run's own limit, and the report it leaves behind is short."""
    seed = report.get("seed")
    assert isinstance(seed, int), "the report carries no seed; the run did not finish"
    boards = report["boards"]
    missing = []
    wrong = []
    for item in scen.wide(_count("RUN_WIDE", "36"), seed):
        got = boards.get(item["name"])
        if got is None:
            missing.append(item["name"])
            continue
        threads, log = oracle.board(item["revs"], item["events"])
        if got != {"threads": threads, "log": log}:
            wrong.append(item["name"])
    assert not missing, "%d wide streams never came back, first: %s" % (
        len(missing), ", ".join(missing[:8]))
    assert not wrong, "wrong on %d wide streams, first: %s" % (
        len(wrong), ", ".join(wrong[:8]))


def test_the_sealed_model_agrees_with_the_recorded_truth(truth):
    """The ground truth is only worth grading against if a second, separately
    written model reaches it from the rule alone."""
    for item in scen.FIXED:
        threads, log = oracle.board(item["revs"], item["events"])
        assert {"threads": threads, "log": log} == truth["fixed"][item["name"]], \
            "the sealed model and the recorded truth differ on %s" % item["name"]


def test_no_stream_faulted(report):
    broken = [n for n, v in report["boards"].items() if "error" in v]
    assert not broken, "the board raised on %d streams: %s" % (
        len(broken), ", ".join(broken[:5]))


def test_the_executed_tree_was_the_one_we_shipped():
    """Everything outside the declared artifacts has to be byte-identical to
    the pristine copy. Counted, then compared: a comparison loop that walks a
    directory that is not there passes every file it never looked at."""
    pristine = pathlib.Path("/pristine")
    live = WORK / "app"
    artifacts = {"note/board.py", "note/rule.py"}
    checked = 0
    for path in sorted(pristine.rglob("*.py")):
        rel = path.relative_to(pristine).as_posix()
        if rel in artifacts:
            continue
        checked += 1
        assert (live / rel).read_bytes() == path.read_bytes(), \
            "%s was modified" % rel
    assert checked >= 4, "only %d frozen files were compared" % checked
