"""Grading for `pack-bind-retire`.

THE FROZEN CONTRACT
===================

The graded artifact is the residency ledger, and nothing else. One row a line:

    <script> <step> ld <pack> <n>...     residents created, in creation order, or `-`
    <script> <step> us <pack> <name> <r> a resident number, or `none`, `bad`, `off`
    <script> <step> dp <pack> <n>        the resident that stopped standing, or `bad`
    <script> <step> rl <n>...            residents released, newest first, or `-`

Every event emits its own row, a `us` row for each hop of a chained use, and exactly one
`rl` row last. That is what makes the artifact tie-free: no quantity in it is a choice, and
there is no representation left over to choose.

Real work - two implementations of the contract agree on all of it by construction:

  * every resident number, and therefore the order in which a load creates residents
  * what every use resolves to, including a repeat of a name the asker has already used
  * the residents released after every event, and the order they are reported in
  * the tokens `none`, `bad`, `off` and `-`

Implementation choice - never graded:

  * how a view is stored, cached or rebuilt; how records are indexed; how the kept set is
    computed; module-private names; whether any shipped helper is called at all

Nothing about how the ledger was produced is inspected. There is no journal, no call tally
and no fingerprint of submitted code, because none of them is needed: the scripts that
decide the grade are built here, from a nonce made after the agent has finished, so a ledger
that matches was produced by something that implements the contract rather than by something
that remembered an answer. The isolation that remains is mechanistic and invisible to any
correct submission - the executed tree outside the five declared artifacts must be
byte-identical to the pristine copy, the reward is root-owned and defaults to 0 before
submitted code loads, the run happens under an unprivileged uid in its own session, and its
survivors are reaped.

Grading is exact and all-or-nothing over two families the run cannot tell apart: the
enumerated scripts, which are checked twice - against a sealed ground truth built before the
agent existed and against the independent model - and the generated scripts, which are
checked against the model alone.

The fence runs both ways on purpose. Releasing a resident that something could still use
fails, and keeping one that nothing can use fails just as hard, so a submission that never
releases anything scores exactly what one that releases everything scores.
"""
import hashlib
import json
import os

import pytest

import cases
import model

LAB = os.environ.get("LAB", "/lab")
PRISTINE = os.environ.get("PRISTINE", "/pristine")

ARTIFACTS = ("hst/vw.py", "hst/bd.py", "hst/ld.py", "hst/rt.py", "hst/od.py")
TAGS = ("ld", "us", "dp", "rl")


@pytest.fixture(scope="module")
def report():
    path = os.path.join(LAB, "out", "rows.txt")
    assert os.path.isfile(path), "the run produced no report at %s" % path
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read()
    try:
        data = json.loads(raw)
    except ValueError as exc:
        pytest.fail("the run's report is not readable: %s" % exc)
    assert isinstance(data, dict), "the run's report is not an object"
    for key, kind in (("rows", list), ("tree", dict), ("errors", list)):
        assert isinstance(data.get(key), kind), "report field %r is missing or wrong" % key
    return data


@pytest.fixture(scope="module")
def scripts():
    d = os.path.join(LAB, "case")
    assert os.path.isdir(d), "no script directory at %s" % d
    out = {}
    for f in sorted(os.listdir(d)):
        if f.endswith(".txt"):
            out[f[:-4]] = os.path.join(d, f)
    assert out, "no scripts were generated"
    return out


@pytest.fixture(scope="module")
def expected(scripts):
    return {nm: model.ledger(nm, p) for nm, p in sorted(scripts.items())}


@pytest.fixture(scope="module")
def produced(report, scripts):
    out = {nm: [] for nm in scripts}
    for row in report["rows"]:
        assert isinstance(row, str), "a ledger row is not a string"
        head = row.split(" ", 1)[0]
        if head in out:
            out[head].append(row)
    return out


def test_run_completed(report, scripts):
    assert report["errors"] == [], "the host raised while running: %s" % report["errors"][:4]
    assert report["seen"] == len(scripts), (
        "the run saw %s scripts, not the %d it was given" % (report["seen"], len(scripts)))


def test_rows_are_well_formed(report, scripts):
    seen = set()
    for row in report["rows"]:
        w = row.split()
        assert len(w) >= 3, "malformed ledger row: %r" % row
        assert w[0] in scripts, "row names a script that was not run: %r" % row
        assert w[1].isdigit(), "row carries no step number: %r" % row
        assert w[2] in TAGS, "row carries an unknown tag: %r" % row
        seen.add(w[0])
    assert seen == set(scripts), (
        "%d script(s) produced no rows at all" % len(set(scripts) - seen))


def test_frozen_tree_is_untouched(report):
    got = report["tree"]
    want = {}
    for base, dirs, files in os.walk(PRISTINE):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for f in sorted(files):
            if f.endswith(".pyc"):
                continue
            p = os.path.join(base, f)
            rel = os.path.relpath(p, PRISTINE).replace(os.sep, "/")
            with open(p, "rb") as fh:
                want[rel] = hashlib.sha256(fh.read()).hexdigest()
    assert len(want) > 10, "the pristine copy holds %d files - it was not found" % len(want)
    frozen = sorted(r for r in want if r not in ARTIFACTS)
    assert len(frozen) == len(want) - len(ARTIFACTS), (
        "expected %d frozen files beside the %d artifacts, found %d"
        % (len(want) - len(ARTIFACTS), len(ARTIFACTS), len(frozen)))
    checked = 0
    for rel in frozen:
        assert rel in got, "the executed tree is missing %s" % rel
        assert got[rel] == want[rel], "%s was changed, and it is not a declared artifact" % rel
        checked += 1
    assert checked == len(frozen), "compared %d files, expected %d" % (checked, len(frozen))
    extra = sorted(r for r in got if r not in want)
    assert not extra, "the executed tree carries files the shipped one does not: %s" % extra[:5]


def test_enumerated_match_the_sealed_ground_truth(produced):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gt.json"),
              "r", encoding="ascii") as fh:
        gt = json.load(fh)
    assert len(gt) == len(cases.FIXED), (
        "the sealed ground truth holds %d scripts, the enumerated set %d"
        % (len(gt), len(cases.FIXED)))
    for nm in sorted(gt):
        assert produced[nm] == gt[nm], first_difference(nm, produced[nm], gt[nm])


def test_every_script_matches_the_model(produced, expected):
    assert len(expected) >= len(cases.FIXED) + 100, (
        "only %d scripts were graded" % len(expected))
    wrong = []
    for nm in sorted(expected):
        if produced[nm] != expected[nm]:
            wrong.append(nm)
    assert not wrong, "%d of %d scripts came out wrong; first: %s" % (
        len(wrong), len(expected), first_difference(wrong[0], produced[wrong[0]],
                                                    expected[wrong[0]]))


def first_difference(nm, got, want):
    for i in range(max(len(got), len(want))):
        a = got[i] if i < len(got) else "<no row>"
        b = want[i] if i < len(want) else "<no row>"
        if a != b:
            return "%s row %d: the host said %r, the contract says %r" % (nm, i + 1, a, b)
    return "%s: ledgers are equal" % nm
