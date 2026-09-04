"""Verifier for the alias settle report task.

THE VERIFIER CONTRACT, frozen before the environment was finished. It lives here
because this is the file the run audit and the quality review read, and because a
contract that lives only in a working note is a contract that goes missing.

What the run produced is in /box/say/out.json, written by /tests/runner.py, the
only process that executed anything the agent wrote. Nothing in this file
imports, execs or subprocesses agent code. It reads that JSON as hostile input
and grades it against /tests/oracle.py, a sealed second implementation of the
same specification that shares no code with the tree, and against /tests/gt.json,
which is root-only and was never visible to the run.

WHAT IS GRADED, on every set, exactly, in order, with no partial credit:

  1. THE ROWS. Everything the machine emitted: each post a run made, each
     sameness and each difference a tag declared, each shut, each filing with the
     key it was filed for, the key it was filed under and the score that stood,
     and the tick the set ended on. Every one of those rows is emitted by
     bind/mc.py, which is not an editable artifact, so the rows record what the
     machine did rather than what a submission says it did. The filings are the
     decisions under examination: when a watched key is filed and what its row
     reads.

  2. THE FILING TABLE. Per watched key, the tick it was filed on and the row it
     carried, collected as the machine ran. Stated honestly this is a cross-check
     rather than a second axis - the rows already carry a filing row apiece, so
     the two cannot disagree unless a submission produced one without the other.
     What it buys is legibility: a key filed one tick early says so in one line,
     where a row index says only that something moved.

TWO SET LISTS, and the second is why an answer key is worth nothing here:

  The enumerated list in cases.py is thirty-six sets, each named for the reading
  it exists to fail, with the must-still-work side of every fence beside the case
  that says must-not, and the three sets that ship in the tree included verbatim.
  It is fixed, it is in the bundle, and its expected rows are in gt.json.

  The differential list is three hundred sets built by gen.py out of RUN_NONCE,
  which test.sh draws from /dev/urandom inside the verifier container after the
  agent has stopped. Those sets did not exist when the submission was written and
  their expected rows are produced by the sealed model after the run, so there is
  no number to assign and no table to paste. The cheat suite makes the point
  directly: one cheat carries gt.json's own bytes, is right on every enumerated
  set, and scores 0.

WHAT IS NOT GRADED, because grading it would measure an implementation choice
rather than a behaviour: how a submission searches the tags, what it caches
between ticks, whether it answers the question one cell at a time or for a whole
group at once, and which of the four declared files it puts the reasoning in.
Five alternative correct implementations are held outside the bundle, in the
authoring repository, and all five are required to score 1. The interpreter's
counts of entries into the decision functions are recorded and compared only as
floors, for the same reason:
a submission that folds the reach search into the readiness test enters one of
them zero times and is correct.

FOUR ATTESTATIONS, because the verifier executes agent code:

  The executed tree outside the four declared artifacts must be byte-identical to
  the pristine copy after the run, and the comparison asserts how many files it
  found before it compares any of them.

  Every sealed machine function must be, as it actually existed in the running
  interpreter at import and again when each set ended, what the pristine sources
  compile to. Nothing is executed to derive that baseline: the sources are
  compiled and the code objects fingerprinted, outside the run, from files the run
  cannot write.

  The interpreter's count of entries into the emitter must equal the number of
  rows, and the instrumentation must still have been armed when each set ended.

  The report must carry the run nonce, so a report planted before the run cannot
  pass.
"""

import hashlib
import json
import os
import types

import pytest

import cases
import gen
import oracle
import runner

REPORT = os.environ.get("RUN_OUT", "/box/say/out.json")
TREE = os.environ.get("APP_DIR", "/box/app")
CLEAN = os.environ.get("PRISTINE_DIR", "/pristine")

OPEN_FILES = ("bind/rch.py", "bind/hold.py", "bind/card.py", "bind/seq.py")

ROW_RULES = ("rep-is-least", "auth-run-then-key", "auth-inside-run",
             "weld-takes-score", "reach-holds-earlier")
ORDER_RULES = ("two-file-one-tick", "two-watch-one-cell", "all-at-the-end")
REACH_RULES = ("wait-for-tag", "two-hop-reach", "three-hop-reach",
               "shut-tag-inert", "tag-inside-cell", "higher-keys-harmless")
BAR_RULES = ("bar-blocks-hop", "bar-blocks-chain", "bar-off-the-step",
             "bar-leaves-a-detour", "bar-arrives-late", "bar-after-weld",
             "weld-then-reach")
PEND_RULES = ("pending-beats", "pending-loses", "pending-in-reach",
              "pending-out-of-reach", "no-post-yet")
GONE_RULES = ("gone-holds-nothing", "gone-frees-a-run-too",
              "one-going-frees-the-next", "neither-frees-the-other",
              "gone-takes-its-tag", "one-going-takes-a-tag",
              "other-tags-keep-working")
IN_TREE = ("plain", "chain", "barred")


def _report():
    try:
        with open(REPORT) as fh:
            blob = json.load(fh)
    except Exception as exc:
        pytest.fail("the run left no readable report: %r" % (exc,))
    if not isinstance(blob, dict):
        pytest.fail("the run's report is not an object")
    for field in ("nonce", "sets", "torn"):
        if field not in blob:
            pytest.fail("the run's report has no %r" % field)
    if not isinstance(blob["sets"], dict) or not isinstance(blob["torn"], dict):
        pytest.fail("the run's report is malformed")
    return blob


BLOB = _report()


def _truth():
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "gt.json")) as fh:
        return json.load(fh)


TRUTH = _truth()


def _made():
    nonce = os.environ.get("RUN_NONCE", "")
    count = int(os.environ.get("RUN_COUNT", "300"))
    return gen.batch(nonce, count)


MADE = _made()


def _said(name):
    got = BLOB["sets"].get(name)
    if got is None:
        pytest.fail("the run reported nothing for %r" % name)
    if not isinstance(got, dict) or "rows" not in got:
        pytest.fail("the run's entry for %r is malformed" % name)
    return got


def _rows(name):
    return [list(r) for r in _said(name)["rows"]]


def _carve(code, path):
    here = code
    for part in path.split("."):
        found = None
        for item in here.co_consts:
            if isinstance(item, types.CodeType) and item.co_name == part:
                found = item
        if found is None:
            return None
        here = found
    return here


def _baseline():
    book = {}
    for rel, path in runner.FROZEN:
        with open(os.path.join(CLEAN, rel), "rb") as fh:
            body = compile(fh.read(), rel, "exec")
        found = _carve(body, path)
        assert found is not None, "no %s in the pristine %s" % (path, rel)
        book[rel + "::" + path] = runner.stamp(found)
    return runner.knot(book)


BASE = _baseline()


def _walk(root):
    out = {}
    for here, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for name in sorted(files):
            if name.endswith(".pyc"):
                continue
            full = os.path.join(here, name)
            rel = os.path.relpath(full, root)
            with open(full, "rb") as fh:
                out[rel] = hashlib.sha256(fh.read()).hexdigest()
    return out


def test_the_run_finished_every_set():
    assert BLOB["torn"] == {}, "the run raised on: %s" % sorted(BLOB["torn"])


def test_the_report_carries_this_run_nonce():
    want = os.environ.get("RUN_NONCE", "")
    assert want, "the harness supplied no nonce"
    assert BLOB["nonce"] == want, "the report was not made by this run"
    assert BLOB["count"] == int(os.environ.get("RUN_COUNT", "300"))


def test_the_executed_tree_was_the_one_we_shipped():
    ours = _walk(CLEAN)
    theirs = _walk(TREE)
    assert len(ours) > 8, "the pristine copy was not found where we left it"
    assert sorted(ours) == sorted(theirs), "the executed tree gained or lost files"
    moved = [rel for rel in sorted(ours)
             if ours[rel] != theirs.get(rel)
             and rel.replace(os.sep, "/") not in OPEN_FILES]
    assert moved == [], "files outside the declared artifacts were changed: %s" % moved


@pytest.mark.parametrize("name", sorted(cases.SETS) + [n for n, _ in MADE])
def test_the_sealed_machine_ran_as_shipped(name):
    got = _said(name)
    assert got["in"] == BASE, "a sealed function was not the shipped one at import"
    assert got["out"] == BASE, "a sealed function was replaced while the set ran"


@pytest.mark.parametrize("name", sorted(cases.SETS) + [n for n, _ in MADE])
def test_the_rows_came_through_the_emitter(name):
    got = _said(name)
    if os.environ.get("NEED_MON") == "1":
        assert got["mode"] == "monitoring", "the interpreter did not do the counting"
    assert got["armed"] is True, "the instrumentation was not armed at the end"
    assert got["hits"]["ev"] == len(got["rows"]), \
        "rows appeared without the emitter running"
    assert got["hits"]["firm"] >= 1
    assert got["hits"]["queue"] >= 1
    assert got["hits"]["card"] >= len(got["fil"])


@pytest.mark.parametrize("name", ROW_RULES)
def test_the_row_a_filing_carries(name):
    assert _rows(name) == TRUTH[name]


@pytest.mark.parametrize("name", ORDER_RULES)
def test_filings_land_in_the_stated_order(name):
    assert _rows(name) == TRUTH[name]


@pytest.mark.parametrize("name", REACH_RULES)
def test_what_an_open_tag_can_still_weld(name):
    assert _rows(name) == TRUTH[name]


@pytest.mark.parametrize("name", BAR_RULES)
def test_what_a_difference_rules_out(name):
    assert _rows(name) == TRUTH[name]


@pytest.mark.parametrize("name", PEND_RULES)
def test_what_a_run_can_still_post(name):
    assert _rows(name) == TRUTH[name]


@pytest.mark.parametrize("name", GONE_RULES)
def test_what_a_line_already_handed_over_changes(name):
    assert _rows(name) == TRUTH[name]


@pytest.mark.parametrize("name", IN_TREE)
def test_the_sets_that_ship_in_the_tree(name):
    assert _rows(name) == TRUTH[name]


def test_every_enumerated_set_was_graded():
    covered = set(ROW_RULES) | set(ORDER_RULES) | set(REACH_RULES) \
        | set(BAR_RULES) | set(PEND_RULES) | set(GONE_RULES) | set(IN_TREE)
    assert covered == set(cases.SETS), \
        "an enumerated set is in the bundle and in no sweep"


@pytest.mark.parametrize("name", sorted(cases.SETS))
def test_the_filing_table_agrees_with_the_rows(name):
    got = _said(name)
    want = {}
    for row in _rows(name):
        if row[0] == "fl":
            want[str(row[2])] = [row[1], row[3], row[4]]
    assert got["fil"] == want


def test_the_answers_are_what_the_sealed_model_says():
    wrong = [name for name in sorted(cases.SETS)
             if oracle.play(cases.SETS[name]) != TRUTH[name]]
    assert wrong == [], "ground truth disagrees with the model on: %s" % wrong


def test_the_sets_made_after_the_agent_stopped():
    bad = []
    for name, text in MADE:
        got = _said(name)
        want = oracle.play(text)
        if [list(r) for r in got["rows"]] != want:
            bad.append(name)
        elif got["fil"] != oracle.filings(want):
            bad.append(name)
        if len(bad) > 6:
            break
    assert bad == [], "sets made after the run: %s" % bad
