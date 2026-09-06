"""Verifier for the batch admit and reclaim task.

THE VERIFIER CONTRACT, frozen before the environment was finished. It lives here
because this is the file the run audit and the quality review read, and because a
contract that lives only in a working note is a contract that goes missing.

What the run produced is in /box/say/out.json, written by /tests/runner.py, the
only process that executed anything the agent wrote. Nothing in this file
imports, execs or subprocesses agent code. It reads that JSON as hostile input
and grades it against /tests/oracle.py, a second implementation of the same
rules that shares no code with the tree, and against /tests/gt.json, which is
root-only and was never visible to the run.

WHAT IS GRADED, on every trace, exactly, in order, with no partial credit:

  THE TIMELINE. Per request: the step it came in and the token it started
  working from, every step it was put out and how many tokens it had by then,
  every step it came back and the token it started again from, and the step it
  finished. Nothing else. Block identities, pool occupancy, eviction order and
  the engine's internal bookkeeping are not compared, because they are the
  machine's business rather than the outcome the work exists to get right - a
  submission that reaches the same timeline by different internal means is
  correct and is required to score 1.

  Every line is emitted by eng/log.py, which is not an editable artifact, so the
  timeline records what the engine did rather than what a submission says it did.

TWO TRACE LISTS, and the second is why an answer key is worth nothing here:

  The enumerated list in cases.py is twenty-nine traces. Thirteen are named for
  the reading of the rules they exist to fail; eleven are named for the ordinary
  behaviour they exist to protect, so that a submission cannot pass by turning
  conservative; three are the traces that ship in the tree, included verbatim, so
  a submission fitted to those is graded on them too. It is fixed, it is in the
  bundle, and its expected timelines are in gt.json.

  The differential list is three hundred traces built by gen.py out of RUN_NONCE,
  which test.sh draws from /dev/urandom inside the verifier container after the
  agent has stopped. Those traces did not exist when the submission was written
  and their expected timelines are produced by the sealed model after the run, so
  there is no number to assign and no table to paste. One cheat carries gt.json's
  own bytes, is right on every enumerated trace, and scores 0.

WHAT IS NOT GRADED, because grading it would measure an implementation choice
rather than a behaviour: how a submission answers the entry question, whether it
plays the step on a copy of the pool or reasons about it arithmetically, what it
caches between steps, and which of the four declared files it puts the reasoning
in. Correct variants are held outside the bundle and all of them are required to
score 1. The interpreter's counts of entries into the four policy hooks are
compared only as floors across the whole run, for the same reason: a submission
that answers the entry question without ever asking where a request would start
again enters one of them fewer times and is still correct.

FOUR ATTESTATIONS, because the verifier executes agent code:

  The executed tree outside the four declared artifacts must be byte-identical to
  the pristine copy after the run, and the comparison asserts how many files it
  found before it compares any of them.

  Every sealed engine function must be, as it actually existed in the running
  interpreter when the tree was imported and again when each trace ended, what
  the pristine sources compile to. Nothing is executed to derive that baseline:
  the sources are compiled and the code objects fingerprinted, outside the run,
  from files the run cannot write.

  The interpreter's count of entries into the emitter must equal the number of
  lines in the timeline, and the instrumentation must still have been armed when
  each trace ended.

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

REPORT = os.environ.get("RUN_OUT", "/box/say/out.json")
TREE = os.environ.get("APP_DIR", "/box/app")
CLEAN = os.environ.get("PRISTINE_DIR", "/pristine")
TRUTH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gt.json")

EDITABLE = ("eng/fit.py", "eng/room.py", "eng/back.py", "eng/pick.py")
FROZEN_FILES = 9

SEALED = (
    "eng/pool.py:keys",
    "eng/pool.py:Pool.occ",
    "eng/pool.py:Pool.has",
    "eng/pool.py:Pool.loose",
    "eng/pool.py:Pool.sweep",
    "eng/pool.py:Pool.take",
    "eng/pool.py:Pool.give",
    "eng/pool.py:Pool.hold",
    "eng/pool.py:Pool.free",
    "eng/log.py:Log.put",
    "eng/rd.py:parse",
    "eng/step.py:Eng.mark",
    "eng/step.py:Eng.enter",
    "eng/step.py:Eng.shed",
    "eng/step.py:Eng.close",
    "eng/step.py:Eng.tick",
    "eng/step.py:Eng.turn",
    "eng/step.py:Eng.run",
)

HOOKS = ("ok", "pick", "at", "order", "victim")


# ---------------------------------------------------------------- the report

def load():
    with open(REPORT) as handle:
        raw = handle.read()
    assert raw.strip(), "the run published nothing"
    return json.loads(raw)


@pytest.fixture(scope="session")
def report():
    return load()


@pytest.fixture(scope="session")
def truth():
    with open(TRUTH) as handle:
        return json.load(handle)


@pytest.fixture(scope="session")
def wanted():
    """Every trace the run should have played, enumerated half first."""
    nonce = os.environ.get("RUN_NONCE", "")
    count = int(os.environ.get("RUN_COUNT", "300"))
    order = [(name, cases.TRACES[name]) for name in sorted(cases.TRACES)]
    order.extend(gen.batch(nonce, count))
    return order


# ------------------------------------------------------- the sealed baseline

def digest(code):
    acc = hashlib.sha256()
    acc.update(code.co_code)
    acc.update(repr(code.co_names).encode("utf-8"))
    acc.update(repr(code.co_varnames).encode("utf-8"))
    for item in code.co_consts:
        if isinstance(item, types.CodeType):
            acc.update(digest(item).encode("utf-8"))
        else:
            acc.update(repr(item).encode("utf-8"))
    return acc.hexdigest()


def inner(code, name):
    for item in code.co_consts:
        if isinstance(item, types.CodeType) and item.co_name == name:
            return item
    return None


def find(where):
    """The code object of one sealed function, compiled from the pristine source."""
    rel, path = where.split(":")
    with open(os.path.join(CLEAN, rel)) as handle:
        top = compile(handle.read(), rel, "exec")
    node = top
    for part in path.split("."):
        node = inner(node, part)
        assert node is not None, "sealed function %s not found in %s" % (path, rel)
    return node


@pytest.fixture(scope="session")
def sealed_fold():
    """The fold runner.py reports, computed here from the pristine sources.

    Nothing is imported or executed to get this: each file is compiled and the
    named code object fingerprinted, from a copy the run cannot write.
    """
    book = {}
    for where in SEALED:
        rel, path = where.split(":")
        book[rel[:-3].replace("/", ".") + ":" + path] = digest(find(where))
    acc = hashlib.sha256()
    for key in sorted(book):
        acc.update(("%s=%s\n" % (key, book[key])).encode("utf-8"))
    return acc.hexdigest()


# ------------------------------------------------------------------- grading

def test_the_run_played_every_trace(report, wanted):
    assert not report["broke"], "traces that threw: %s" % sorted(report["broke"])[:5]
    assert len(wanted) == len(cases.TRACES) + int(report["count"])
    missing = [name for name, _ in wanted if name not in report["traces"]]
    assert not missing, "traces with no timeline: %s" % missing[:5]
    assert len(report["traces"]) == len(wanted)


def test_the_report_carries_the_run_nonce(report):
    assert report["nonce"] == os.environ.get("RUN_NONCE", "")
    assert len(report["nonce"]) >= 32


def test_enumerated_timelines(report, truth):
    assert sorted(truth) == sorted(cases.TRACES), "gt.json is out of step with cases.py"
    wrong = []
    for name in sorted(cases.TRACES):
        got = [list(x) for x in report["traces"][name]["lines"]]
        if got != [list(x) for x in truth[name]]:
            wrong.append(name)
    assert not wrong, "timelines that differ on the enumerated traces: %s" % wrong[:6]


def test_generated_timelines(report, wanted):
    wrong = []
    for name, text in wanted:
        if name in cases.TRACES:
            continue
        got = [list(x) for x in report["traces"][name]["lines"]]
        if got != [list(x) for x in oracle.play(text)]:
            wrong.append(name)
    assert not wrong, "%d of the generated traces differ, first: %s" % (
        len(wrong), wrong[:6])


# -------------------------------------------------------------- attestations

def test_the_tree_outside_the_artifacts_is_untouched():
    seen = []
    for here, _, names in os.walk(CLEAN):
        for name in sorted(names):
            full = os.path.join(here, name)
            rel = os.path.relpath(full, CLEAN)
            if rel in EDITABLE or rel.endswith(".pyc") or "__pycache__" in rel:
                continue
            seen.append(rel)
    assert len(seen) == FROZEN_FILES, "expected %d frozen files, walked %d: %s" % (
        FROZEN_FILES, len(seen), sorted(seen))
    for rel in seen:
        with open(os.path.join(CLEAN, rel), "rb") as handle:
            was = handle.read()
        run = os.path.join(TREE, rel)
        assert os.path.isfile(run), "the run is missing %s" % rel
        with open(run, "rb") as handle:
            now = handle.read()
        assert now == was, "%s was changed under the run" % rel


def test_the_sealed_functions_are_the_pristine_ones(report, sealed_fold):
    off = []
    for name in sorted(report["traces"]):
        seen = report["traces"][name]
        if seen["open"] != sealed_fold or seen["shut"] != sealed_fold:
            off.append(name)
    assert not off, "sealed engine functions were not themselves on: %s" % off[:6]


def test_every_line_came_through_the_emitter(report):
    off = []
    for name in sorted(report["traces"]):
        seen = report["traces"][name]
        if not seen["armed"] or seen["hits"]["put"] != len(seen["lines"]):
            off.append(name)
    assert not off, "the emitter count does not match the timeline on: %s" % off[:6]


def test_the_policy_was_asked(report):
    total = dict((h, 0) for h in HOOKS)
    for name in report["traces"]:
        for hook in HOOKS:
            total[hook] += report["traces"][name]["hits"].get(hook, 0)
    silent = [h for h in HOOKS if total[h] == 0]
    assert not silent, "policy hooks never entered across the whole run: %s" % silent
