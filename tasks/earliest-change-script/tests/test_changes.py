"""Grading. Reads what the submitted module produced and works out, here,
what it should have produced.

Nothing the report says about itself is treated as evidence: how many cases
there were, and what they were, comes from the case generator in this package
and from the seed this account was handed, never from the file the sandbox
wrote into.
"""

import json
import os
import pathlib
import sys

import pytest

import casegen
import oracle
import reference

REPORT = pathlib.Path(os.environ.get("REPORT", "/tmp/results/report.json"))
SEED = int(os.environ.get("RUN_SEED", "0"))
N_RANDOM = 12000

FIXED = list(casegen.FIXED)
RANDOM = casegen.random_cases(N_RANDOM, SEED)
STRUCTURED = casegen.structured_cases()
ALL_CASES = FIXED + RANDOM + STRUCTURED


def load():
    if not REPORT.exists():
        pytest.fail("the harness produced no report at %s" % REPORT)
    return json.loads(REPORT.read_text() or "{}")


R = load()


def as_pairs(value):
    if not isinstance(value, list):
        return None
    return [tuple(item) for item in value]


def compare(cases, answers, expected, label, offset=0):
    wrong = []
    for position, (before, after) in enumerate(cases):
        got = as_pairs(answers[offset + position])
        want = [tuple(op) for op in expected(before, after)]
        if got != want:
            wrong.append({"before": before[:24], "after": after[:24],
                          "got": answers[offset + position][:24]
                          if isinstance(answers[offset + position], list)
                          else answers[offset + position],
                          "expected": [list(op) for op in want][:24]})
    assert not wrong, "%d of %d %s cases are wrong, first few:\n%s" % (
        len(wrong), len(cases), label, json.dumps(wrong[:6], indent=2))


def cases_answers():
    block = R.get("cases") or {}
    if "error" in block:
        pytest.fail("the submitted module failed on the case block: %s"
                    % block["error"])
    answers = block.get("answers")
    assert isinstance(answers, list), "the harness recorded no answers"
    assert len(answers) == len(ALL_CASES), (
        "expected %d answers, the report holds %d"
        % (len(ALL_CASES), len(answers)))
    return answers


def test_the_module_ran_at_all():
    cases_answers()


def test_the_grading_framework_was_left_alone():
    marks = list((R.get("cases") or {}).get("tamper") or [])
    marks += list((R.get("medium") or {}).get("tamper") or [])
    for entry in R.get("timed") or []:
        marks += list(entry.get("tamper") or [])
    assert marks == [], "; ".join(marks)


def test_no_submitted_module_reached_this_process():
    assert "change_script" not in sys.modules


def test_the_two_models_agree_before_anything_larger_is_graded():
    """The medium and timed blocks are graded against the fast implementation
    because the definitional one cannot run at that size. This is the check
    that buys the right to do that."""
    disagree = [(before, after) for before, after in FIXED + STRUCTURED
                if [tuple(op) for op in reference.changes(before, after)]
                != [tuple(op) for op in oracle.script(before, after)]]
    assert not disagree, "%d cases split the two models" % len(disagree)


@pytest.mark.parametrize("engine", ["frontier", "row", "pairs"])
def test_every_engine_of_the_fast_model_is_checked(engine):
    """The fast implementation dispatches between three engines and the short
    cases all land on the same one, so the test above never exercises the other
    two. Between them they produce the expected answers for two thirds of the
    timed block, so each is forced on here and held to the definitional model
    on its own. A hybrid only ever exercised on one side of its own crossover
    is a hybrid whose other sides are untested."""
    disagree = [(before, after) for before, after in FIXED + STRUCTURED
                if [tuple(op) for op in reference.changes(before, after, engine)]
                != [tuple(op) for op in oracle.script(before, after)]]
    assert not disagree, "%d cases split the %s engine from the model" % (
        len(disagree), engine)


def test_fixed_cases():
    compare(FIXED, cases_answers(), oracle.script, "fixed")


def test_random_cases():
    compare(RANDOM, cases_answers(), oracle.script, "random",
            offset=len(FIXED))


def test_enumerated_cases():
    compare(STRUCTURED, cases_answers(), oracle.script, "enumerated",
            offset=len(FIXED) + len(RANDOM))


def medium_block():
    block = R.get("medium") or {}
    if "error" in block:
        pytest.fail("the medium block did not finish: %s" % block["error"])
    answers = block.get("answers")
    assert isinstance(answers, list), "the medium block recorded no answers"
    assert len(answers) == casegen.MEDIUM_COUNT
    return answers


def test_medium_cases_are_answered_correctly():
    compare(casegen.medium_cases(SEED), medium_block(), reference.changes,
            "medium")


def test_medium_block_stays_inside_its_budget():
    medium_block()
    seconds = R.get("medium_seconds")
    assert isinstance(seconds, (int, float)), "no timing for the medium block"
    assert seconds <= casegen.MEDIUM_BUDGET, (
        "the medium block took %.1f seconds against a budget of %.1f"
        % (seconds, casegen.MEDIUM_BUDGET))


def timed_entries():
    entries = R.get("timed")
    assert isinstance(entries, list), "no timed block in the report"
    assert len(entries) == len(casegen.TIMED_SHAPES)
    return entries


def test_large_cases_are_answered_correctly():
    entries = timed_entries()
    wrong = []
    for index, entry in enumerate(entries):
        before, after = casegen.timed_case(index, SEED)
        kind = casegen.TIMED_SHAPES[index][0]
        if "error" in entry:
            wrong.append("case %d (%s): %s" % (index, kind, entry["error"]))
            continue
        got = as_pairs(entry.get("answer"))
        want = [tuple(op) for op in reference.changes(before, after)]
        if got != want:
            first = None
            for position, pair in enumerate(want):
                if got is None or position >= len(got) or got[position] != pair:
                    first = position
                    break
            wrong.append(
                "case %d (%s, %d lines against %d): %d moves expected, %s "
                "given, first difference at move %s"
                % (index, kind, len(before), len(after), len(want),
                   "none" if got is None else str(len(got)), first))
    assert not wrong, "\n".join(wrong)


def test_large_cases_stay_inside_their_budget():
    slow = []
    for index, entry in enumerate(timed_entries()):
        seconds = entry.get("seconds")
        if not isinstance(seconds, (int, float)) \
                or seconds > casegen.TIMED_BUDGET:
            slow.append("case %d (%s) took %s seconds"
                        % (index, casegen.TIMED_SHAPES[index][0], seconds))
    assert not slow, "budget is %.1f seconds a case:\n%s" % (
        casegen.TIMED_BUDGET, "\n".join(slow))
