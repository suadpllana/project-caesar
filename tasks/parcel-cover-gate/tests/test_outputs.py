"""The grader. Root, after the run, executing nothing the agent wrote.

What is graded, and why passing it means the fabric was rebuilt rather than
guessed at.

  The rows. Every read a feed makes and every settling of a shown map, in the
  order the ops produced them, exactly. There is no partial credit and no
  tolerance anywhere: a value is a value.

  The picture each worker is left holding. A submission can get every read right
  by never letting anything go up when a read is not imminent, and the closing
  picture is what makes that not work.

  Two feed sets. The named ones are baked, and the run may read them. The other
  three hundred are built from a nonce drawn out of /dev/urandom once the agent
  has stopped, so they did not exist while the submission was being written and
  their rows are worked out here by `oracle.py`, which the run cannot open and
  which shares no code with the tree.

  That the counted work happened. Versions and parcels are made in files the four
  editable ones may not touch, and the interpreter itself counts entries into
  those two functions from a closure with no name inside the tree. The floors
  come from the feed text: a submission cannot come in under them without having
  stopped the counting, which is itself reported and checked.

  That the tree that ran was the tree we shipped. Two guards, because they catch
  different things. The digests the run took, before and after each feed, catch a
  function swapped out while the feed was running. They cannot catch one swapped
  at import time, before the first digest, so the baseline they are held against
  is derived here, by compiling the untouched sources - a file the run cannot
  write, in a directory the run cannot reach.
"""

import hashlib
import json
import os
import sys
import types

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cases
import gen
import oracle
import runner

OUT = os.environ.get("RUN_OUT", "/work/run/out.json")
APP = os.environ.get("APP_DIR", "/work/app")
PURE = os.environ.get("PRISTINE_DIR", "/pristine")
HERE = os.path.dirname(os.path.abspath(__file__))

OPEN = ("bay/desc.py", "bay/cov.py", "bay/stand.py", "bay/gate.py")

sys.setrecursionlimit(30000)


def _load():
    with open(OUT, "rb") as fh:
        raw = fh.read()
    if not raw.strip():
        pytest.fail("the run published nothing")
    try:
        return json.loads(raw.decode("utf-8"))
    except ValueError as exc:
        pytest.fail("the run published something that is not a report: %s" % exc)


REPORT = _load()
NONCE = os.environ.get("RUN_NONCE", "")
COUNT = int(os.environ.get("RUN_COUNT", "300"))
MADE = gen.batch(NONCE, COUNT)


def _feeds():
    out = [(n, cases.FEEDS[n]) for n in sorted(cases.FEEDS)]
    out.extend(MADE)
    return out


FEEDS = _feeds()


def _report(name):
    got = REPORT.get("reports", {}).get(name)
    if got is None:
        pytest.fail("no report for feed %s" % name)
    return got


def _want(text):
    """The second reading's answer, through JSON so tuples compare as rows do."""
    rows, tail = oracle.play(text)
    return tuple(json.loads(json.dumps([[list(r) for r in rows],
                                        [list(t) for t in tail]])))


def _walk(root):
    out = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for name in sorted(files):
            if name.endswith(".pyc"):
                continue
            full = os.path.join(base, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            with open(full, "rb") as fh:
                out[rel] = hashlib.sha256(fh.read()).hexdigest()
    return out


def _baseline():
    """Digests of the sealed functions, from sources the run could not write."""
    book = {}
    for rel, path in runner.SEALED:
        with open(os.path.join(PURE, rel), "rb") as fh:
            top = compile(fh.read(), rel, "exec")
        found = None
        for bit in top.co_consts:
            if isinstance(bit, types.CodeType) and bit.co_name == path:
                found = bit
        assert found is not None, "no %s in pristine %s" % (path, rel)
        book[rel + "::" + path] = runner.one(found)
    return runner.tie(book)


def test_the_run_finished_every_feed():
    assert REPORT.get("errors") == {}, REPORT.get("errors")
    assert REPORT.get("nonce") == NONCE
    assert REPORT.get("count") == COUNT
    assert sorted(REPORT.get("reports", {})) == sorted(n for n, _ in FEEDS)


def test_the_named_feeds_match_the_answers():
    with open(os.path.join(HERE, "gt.json")) as fh:
        truth = json.load(fh)
    assert sorted(truth) == sorted(cases.FEEDS)
    for name in sorted(truth):
        got = _report(name)
        assert got["rows"] == truth[name]["rows"], name
        assert got["tail"] == truth[name]["tail"], name


def test_the_named_answers_are_what_the_second_reading_says():
    with open(os.path.join(HERE, "gt.json")) as fh:
        truth = json.load(fh)
    for name in sorted(cases.FEEDS):
        rows, tail = _want(cases.FEEDS[name])
        assert truth[name]["rows"] == rows, name
        assert truth[name]["tail"] == tail, name


@pytest.mark.parametrize("lot", range(10))
def test_the_generated_feeds_match(lot):
    step = (len(MADE) + 9) // 10
    seen = 0
    for name, text in MADE[lot * step:(lot + 1) * step]:
        rows, tail = _want(text)
        got = _report(name)
        assert got["rows"] == rows, name
        assert got["tail"] == tail, name
        seen += 1
    assert seen > 0 or len(MADE) < lot * step + 1


def test_every_read_a_feed_asks_for_comes_back():
    """A submission cannot answer fewer questions than it was asked."""
    for name, text in FEEDS:
        asked = sum(1 for line in text.splitlines() if line.split()[:1] == ["rd"])
        rows = _report(name)["rows"]
        assert sum(1 for r in rows if r[0] == "rd") == asked, name


def test_the_rows_arrived_in_step_order():
    for name, _ in FEEDS:
        steps = [r[1] for r in _report(name)["rows"]]
        assert steps == sorted(steps), name


def test_the_sealed_functions_were_the_shipped_ones():
    want = _baseline()
    for name, _ in FEEDS:
        got = _report(name)
        assert got["in"] == want, name
        assert got["out"] == want, name


def test_the_interpreter_was_still_counting():
    """The counting has to be live at the end, and by the strong route.

    `sys.monitoring` arrived in 3.12 and the verifier image is 3.12, so
    "monitoring" is what a real run reports and anything else means the
    instrumentation was never armed the way it was meant to be. The profile
    fallback exists for authoring hosts on 3.11, where `authoring/trial.py`
    sets ALLOW_PROFILE; nothing in the shipped `test.sh` sets it, so a run
    inside the container cannot fall back to it.
    """
    soft = os.environ.get("ALLOW_PROFILE") == "1"
    for name, _ in FEEDS:
        got = _report(name)
        assert got["on"] is True, name
        if not soft:
            assert got["via"] == "monitoring", name


def test_the_counted_work_happened():
    for name, text in FEEDS:
        lines = [line.split() for line in text.splitlines() if line.split()]
        made = sum(1 for bit in lines if bit[0] in ("wr", "rm"))
        packs = sum(1 for bit in lines if bit[0] == "pb")
        ran = _report(name)["ran"]
        assert ran["run"] >= 1, name
        assert ran["make"] >= made, (name, ran["make"], made)
        assert ran["pack"] >= packs, (name, ran["pack"], packs)


def test_the_tree_that_ran_was_the_one_we_shipped():
    here, there = _walk(APP), _walk(PURE)
    assert set(here) == set(there), sorted(set(here) ^ set(there))
    checked = 0
    for rel in sorted(there):
        if rel in OPEN:
            continue
        assert here[rel] == there[rel], rel
        checked += 1
    assert checked >= 5, "compared %d files, which is not the tree" % checked
