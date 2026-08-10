"""Grading. Reads what the reader answered; works out the truth here.

Runs under a different account, never imports the submitted module, and takes
every expected answer from the models in oracle.py, which the account that ran
the reader cannot open.
"""

import json
import os
import pathlib
import random
import sys

import pytest

import casegen
import oracle

REPORT = pathlib.Path(os.environ.get("REPORT", "/tmp/results/report.json"))
SEED = int(os.environ["RUN_SEED"])

SMALL = casegen.small_manifest()
WIDE = casegen.wide_manifest()
SMALL_FILTERS = casegen.small_filters()
WIDE_FILTERS = casegen.wide_filters()

# Worked out once. The small block is graded by trying every choice there is,
# which is affordable exactly once and not twice.
SMALL_TRUTH = [oracle.plan_definitional(SMALL, f) for f in SMALL_FILTERS]
WIDE_TRUTH = None


def wide_truth():
    global WIDE_TRUTH
    if WIDE_TRUTH is None:
        model = oracle.Truth(WIDE)
        WIDE_TRUTH = [model.plan(f) for f in WIDE_FILTERS]
    return WIDE_TRUTH


def load():
    if not REPORT.exists():
        pytest.fail("the harness produced no report at %s" % REPORT)
    try:
        return json.loads(REPORT.read_text() or "{}")
    except Exception as exc:
        pytest.fail("the report is not readable: %s" % exc)


R = load()


def test_the_reader_ran():
    if "error" in R:
        pytest.fail("the submitted module did not survive the run:\n"
                    + str(R["error"]))
    assert R.get("plain"), "the harness recorded no answers"
    assert R.get("held"), "the harness recorded no answers from Reader"


def test_no_attempt_to_reach_the_grading_framework():
    attempts = R.get("tamper") or []
    assert attempts == [], "; ".join(attempts)


def test_the_submitted_module_never_reached_this_process():
    leaked = [m for m in sys.modules if m.split(".")[0] == "file_reads"]
    assert leaked == [], "grading imported submitted code: %s" % leaked


def test_every_block_was_asked():
    want = len(SMALL_FILTERS) + len(WIDE_FILTERS)
    for key in ("plain", "held"):
        answers = R.get(key)
        assert isinstance(answers, list), (
            "%s holds no list of answers: %s" % (key, json.dumps(answers)[:200]))
        assert len(answers) == want, (
            "%s holds %d answers for %d filters" % (key, len(answers), want))


def _check(key, offset, filters, truth, note):
    answers = R.get(key)
    if not isinstance(answers, list) or len(answers) < offset + len(filters):
        pytest.fail("the harness has no answers to grade here")
    bad = []
    for i, f in enumerate(filters):
        got = answers[offset + i]
        want = truth[i]
        if got != want:
            bad.append({"filter": f, "got": got, "expected": want})
    assert not bad, (
        "%d of %d wrong through %s. %s\n%s"
        % (len(bad), len(filters), key, note,
           json.dumps(bad[:4], indent=2, default=str)))


def test_small_block():
    _check("plain", 0, SMALL_FILTERS, SMALL_TRUTH,
           "Graded by trying every choice of a code, or of nothing at all, "
           "for every field the file or the filter mentions.")


def test_small_block_through_reader():
    _check("held", 0, SMALL_FILTERS, SMALL_TRUTH,
           "Both entry points have to answer alike.")


def test_wide_block():
    _check("plain", len(SMALL_FILTERS), WIDE_FILTERS, wide_truth(),
           "A choice agreeing with every recorded pair separately is not the "
           "same as one choice agreeing with all of them at once, and a field "
           "with nothing in it answers a condition neither way.")


def test_wide_block_through_reader():
    _check("held", len(SMALL_FILTERS), WIDE_FILTERS, wide_truth(),
           "Both entry points have to answer alike.")


def test_the_two_ground_truth_models_agree():
    """The wide and timed blocks are graded by the searching model, so it has
    to say what trying every choice says. Checked on fresh instances, inside
    the four fields where trying every choice is affordable."""
    rng = random.Random(SEED ^ 0x51D3)
    manifest = [casegen._entry(rng, casegen.SMALL_COLUMNS,
                               rng.randint(1, 5),
                               rng.choice([3, 5, 9]),
                               rng.choice([0.5, 0.85, 1.0]),
                               rng.choice([0.0, 0.35, 0.7]))
                for _ in range(6)]
    manifest.append({"pairs": {}})
    disagreed = []
    for _ in range(30):
        f = casegen._grow(rng, casegen.SMALL_COLUMNS)
        if oracle.plan_search(manifest, f) != oracle.plan_definitional(
                manifest, f):
            disagreed.append(f)
    assert not disagreed, (
        "the two ground-truth models disagree:\n"
        + json.dumps(disagreed[:2], indent=2))


def test_the_searching_model_misses_no_witness():
    """The searching model cannot invent a file to read -- it reads the choice
    out and puts it back through the definitional checks before it says yes.
    What it could do is miss one, and that no longer has a brute force to catch
    it at twelve fields. So throw complete choices at the wide manifest, keep
    the ones that genuinely are witnesses, and insist the model found those
    files."""
    rng = random.Random(SEED ^ 0x2C7B)
    model = oracle.Truth(WIDE)
    missed = []
    for _ in range(40):
        f = casegen._grow(rng, casegen.COLUMNS)
        plan = set(model.plan(f))
        for index in rng.sample(range(len(WIDE)), 25):
            entry = WIDE[index]
            if index in plan:
                continue
            unset = set(entry.get("unset") or [])
            for _ in range(60):
                row = {}
                for col in casegen.COLUMNS:
                    if col in unset and rng.random() < 0.3:
                        row[col] = None
                    else:
                        row[col] = rng.randrange(casegen.CODES)
                if _agrees(entry, row) and oracle.evaluate(f, row) == oracle.TRUE:
                    missed.append({"file": index, "filter": f, "choice": row})
                    break
    assert not missed, (
        "the searching model skipped a file a witness exists for:\n"
        + json.dumps(missed[:2], indent=2, default=str))


def _agrees(entry, row):
    for name, table in (entry.get("pairs") or {}).items():
        i = row.get(name[0])
        j = row.get(name[1])
        if i is None or j is None:
            continue
        if not (table[i] >> j) & 1:
            return False
    return True


def test_timed_workload():
    timed = R.get("timed") or {}
    assert not timed.get("error"), (
        "the timed run did not finish: %s" % timed.get("error"))
    assert timed.get("digest"), "the timed run produced no answer"
    manifest = casegen.timed_manifest(SEED)
    filters = casegen.timed_filters(SEED)
    model = oracle.Truth(manifest)
    expected = casegen.digest(SEED, [model.plan(f) for f in filters])
    assert timed["digest"] == expected, (
        "the answers over the %d file workload are not the right ones. The "
        "manifest and the %d filters both come from this run's seed, so this "
        "is a correctness failure on the large workload rather than a timing "
        "one." % (len(manifest), len(filters)))


def test_timed_workload_inside_the_budget():
    timed = R.get("timed") or {}
    assert not timed.get("error"), (
        "the timed run did not finish: %s" % timed.get("error"))
    assert timed["seconds"] <= casegen.TIMED_BUDGET, (
        "answering %d filters over %d files took %.1f seconds against a budget "
        "of %.1f."
        % (casegen.TIMED_QUERIES, casegen.TIMED_FILES, timed["seconds"],
           casegen.TIMED_BUDGET))
