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
    raw = (WORK / "out.json").read_text()
    return json.loads(raw)


@pytest.fixture(scope="module")
def report():
    return _report()


@pytest.fixture(scope="module")
def truth():
    return json.loads(TRUTH.read_text())


def _streams(seed):
    return list(scen.FIXED) + scen.generated(
        int(os.environ.get("RUN_COUNT", "300")), seed)


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
    assert isinstance(seed, int)
    boards = report["boards"]
    wrong = []
    for item in scen.generated(int(os.environ.get("RUN_COUNT", "300")), seed):
        threads, log = oracle.board(item["revs"], item["events"])
        want = {"threads": threads, "log": log}
        if boards.get(item["name"]) != want:
            wrong.append(item["name"])
    assert not wrong, "wrong on %d generated streams, first: %s" % (
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
