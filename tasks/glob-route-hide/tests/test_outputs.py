"""Grading. Runs as root, after the worker has finished, and never executes submitted code.

FROZEN CONTRACT
---------------
The agent supplies the five resolution files under `/app/fe/`: `vis.py`, `own.py`, `glob.py`,
`fix.py` and `say.py`. Everything else - the driver `run_res.py`, the reader `fe/rd.py`, the flag
helper `fe/flag.py` and the sample programs - is the verifier's own pristine copy, so only those
five can change what a program prints. The driver calls `settle(prog)` in `fix.py` once per
program and `line(prog, tab, i)` in `say.py` once per reference.

Graded, and settled the same way by the sealed model and the reference written apart:

   1  a line ending `if F` exists only while flag F is on, `if !F` only while it is off, and an
      absent line neither binds nor gives
   2  a module is inside every module whose path is a dot-prefix of its own; a `pub` line is
      seen from every module and any other line from its own module and every module inside
      it; a module sees its parent's names only through its own lines
   3  `use P::N as K` gives, under K, each candidate P has under N that the importing module can
      see, seen from where both the candidate and the line are seen
   4  `use P::*` does the same under every name the importing module does not bind itself
   5  a module that has a present item or explicit import line for a name has under it exactly
      what those lines give, even nothing, and nothing from its globs, whoever is asking
   6  a candidate reached by several chains counts once, seen from every module any chain allows
   7  a candidate is had only through a chain of lines ending at its item line; a cycle alone
      gives nothing; an import from an undeclared module gives nothing
   8  one candidate prints `module.name`; none prints `broken` when the referencing module binds
      the name itself and `unresolved` otherwise; more print `ambiguous` and every candidate
   9  candidates of an ambiguity follow the order of their item lines in the file
  10  one line per `ref` line, in file order: module, name, outcome, single spaces

Implementation choice, and not graded: how holdings are stored, the order modules are visited,
whether visibility is kept as a depth or a path, and any internal naming. Not a free choice,
and not asserted in this file either: the whole exam has to finish inside the worker's 60
second clock, which the two scale families make impossible for any structure that resolves one
(module, name) pair at a time.

Hand cases are checked against `seal/gt.json`, frozen from the model and checked by hand before
this file was written. Generated programs are rebuilt here from the seed, which the submission
never saw, and checked against the sealed model; the model must first reproduce `gt.json`
exactly, so a model that had drifted could not quietly redefine correct.
"""
import json
import os
import pathlib
import sys

import pytest

import cases
import exam

SEAL = os.environ.get("GRH_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("GRH_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("GRH_LOGS", "/logs/verifier"))


def _produced():
    """Every byte here came from a process that ran submitted code. Parse it defensively."""
    try:
        raw = json.loads(OUT.read_text(encoding="utf-8"))
    except Exception as exc:
        pytest.fail("the worker left no readable record: %s" % exc)
    if not isinstance(raw, list):
        pytest.fail("the worker record is not a list")
    by = {}
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            pytest.fail("a worker record entry is malformed")
        if item["name"] in by:
            pytest.fail("the worker recorded %s twice" % item["name"])
        by[item["name"]] = item
    return by


def _lines(item):
    got = item.get("got")
    if got is None:
        pytest.fail("the resolver raised or returned nothing: %s" % (item.get("err"),))
    if not isinstance(got, list) or not all(isinstance(x, str) for x in got):
        pytest.fail("the resolver did not return a list of lines")
    return got


@pytest.fixture(scope="module")
def produced():
    return _produced()


@pytest.fixture(scope="module")
def truth():
    return json.loads(GT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def graded():
    """The exam as the grader rebuilds it from the seed: the only copy that is trusted."""
    seed = (LOGS / "nonce").read_text(encoding="utf-8").strip()
    per = int((LOGS / "per").read_text(encoding="utf-8").strip())
    return exam.everything(seed, per)


# --- the sealed side has to agree with itself before it judges anything -------------------

def test_frozen_truth_matches_the_model(truth):
    """gt.json was frozen from the model; if the two have drifted apart, grade nothing."""
    assert sorted(truth) == sorted(cases.ORDER)
    for name in cases.ORDER:
        assert model.expect(cases.prog(name)) == truth[name], name


# --- every exam program was run, and run on the text that was graded ----------------------

def test_the_worker_ran_the_whole_exam(produced, graded):
    wanted = {name for _fam, name, _lines in graded}
    assert set(produced) == wanted, "worker ran %d programs, the exam has %d" % (
        len(produced), len(wanted))
    for _fam, name, lines in graded:
        assert produced[name].get("sig") == exam.digest(lines), "%s was not the graded text" % name


# --- the enumerated programs: one per decision, plus both sides of each fence -------------

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_case(produced, truth, name):
    assert name in produced, "no record for hand case %s" % name
    assert _lines(produced[name]) == truth[name]


# --- programs generated from a seed drawn after the agent's container was gone ------------

def test_every_generated_program_matches(produced, graded):
    made = [(fam, name, lines) for fam, name, lines in graded if fam != "hand"]
    assert len(made) >= 400, "generated population too small: %d" % len(made)
    bad = []
    for fam, name, lines in made:
        item = produced.get(name)
        if item is None:
            bad.append((name, "missing"))
            continue
        got = item.get("got")
        if got != model.expect(lines):
            bad.append((name, "raised" if got is None else "lines differ"))
    assert not bad, "%d of %d generated programs wrong, first: %s" % (len(bad), len(made), bad[:4])


def test_every_family_is_represented(graded):
    fams = {fam for fam, _name, _lines in graded if fam != "hand"}
    assert fams == {f for f, _big in exam.gen.FAMILIES}
