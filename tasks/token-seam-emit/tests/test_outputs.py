"""Grading for `token-seam-emit`.

THE FROZEN CONTRACT
===================

The graded artifact is the release point at every decode step of every request, and the
finish record. Nothing else is graded.

    <req> em <step> <hex>     bytes released at this step, hex, or `-` when none
    <req> fi <step> <reason>  reason is exactly one of: stop, eos, length

Every step emits exactly one `em` row, including a step that releases nothing and including
the final step, and every request emits exactly one `fi` row after its last `em` row. That
is what makes the artifact tie-free: "release as soon as it is safe" has a unique maximal
answer at every step, and there is no choice of representation left over.

Real work - two correct implementations agree on all of it by construction:

  * the release point at every step, byte for byte
  * the step the request finishes on, and the reason
  * the tail dropped when an occurrence ends the request

Implementation choice - never graded:

  * how the matcher is built (rescan, failure function, automaton), how the pending bytes
    are represented, module-private names, whether the frozen helpers are called at all

Grading is exact and all-or-nothing over three families that the run cannot tell apart: the
enumerated requests, which are checked twice - against a sealed ground truth built before
the agent existed, and against the independent model - and three hundred generated requests
plus the wide family, which are checked against the independent model alone, because they
are made from a nonce created after the agent has already finished.

The fence runs both ways on purpose. Releasing a byte early fails, and holding back a byte
that was already safe to release fails just as hard, so an implementation that plays safe by
holding everything until the end scores exactly what one that releases everything
immediately scores.

WHY PASSING MEANS THE WORK WAS DONE
===================================

The rows are compared against a model that was written from the contract rather than from
the reference, and recomputes every quantity from scratch at every step. Beyond the rows:
the executed tree outside the four declared artifacts must be byte-identical to the pristine
copy, and the comparison asserts how many files it found before it compares any of them,
because a comparison against a directory that is not there passes every file it never looked
at. Every frozen entry point is fingerprinted as it actually stood in the running
interpreter and checked against a digest this grader derives by compiling the pristine
source itself, so rebinding a function is caught the way editing its file already was. The
interpreter's own count of entries into the release module must account for every row
emitted, so a submission that prints rows without running the machine has nothing to show
for them. No submitted code is imported here.
"""
import hashlib
import json
import os

import pytest

import cases
import model
import oracle

LAB = os.environ.get("LAB", "/lab")
PRISTINE = os.environ.get("PRISTINE", "/pristine")
HERE = os.path.dirname(os.path.abspath(__file__))

ARTIFACTS = ("strm/sm.py", "strm/hb.py", "strm/rel.py", "strm/fin.py")
FROZEN = (
    ("tok.vocab", "bs"),
    ("tok.vocab", "sp"),
    ("tok.decode", "lead"),
    ("strm.req", "run"),
    ("strm.req", "parse"),
    ("strm.req", "gate"),
    ("strm.req", "hx"),
)
RUN_LIMIT_SECS = 900.0


# ---------------------------------------------------------------- loading the run

@pytest.fixture(scope="module")
def report():
    """The run's own report, treated as hostile input from here on."""
    path = os.path.join(LAB, "out", "rows.txt")
    assert os.path.isfile(path), "the run produced no report at %s" % path
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read()
    try:
        data = json.loads(raw)
    except ValueError as exc:
        pytest.fail("the run's report is not readable: %s" % exc)
    assert isinstance(data, dict), "the run's report is not an object"
    for key, kind in (("rows", list), ("tally", dict), ("marks", dict), ("tree", dict),
                      ("errors", list)):
        assert isinstance(data.get(key), kind), "report field %r is missing or wrong" % key
    return data


@pytest.fixture(scope="module")
def specs():
    """Every graded request, keyed by name, parsed from the files the run was given."""
    out = {}
    reqdir = os.path.join(LAB, "req")
    assert os.path.isdir(reqdir), "no request directory at %s" % reqdir
    for f in sorted(os.listdir(reqdir)):
        if not f.endswith(".txt"):
            continue
        out[f[:-4]] = read_spec(os.path.join(reqdir, f))
    assert out, "no requests were generated"
    return out


def read_spec(path):
    floor = cap = 0
    stops = []
    ids = []
    with open(path, "r", encoding="ascii") as fh:
        for line in fh:
            w = line.split()
            if not w:
                continue
            if w[0] == "fl":
                floor = int(w[1])
            elif w[0] == "cp":
                cap = int(w[1])
            elif w[0] == "sx":
                stops.append(bytes.fromhex(w[1]))
            elif w[0] == "id":
                ids.extend(int(x) for x in w[1:])
    return (floor, cap, stops, ids)


@pytest.fixture(scope="module")
def vocab():
    """The piece table, read from the pristine tree rather than from the executed one."""
    ns = {}
    path = os.path.join(PRISTINE, "tok", "vocab.py")
    with open(path, "r", encoding="utf-8") as fh:
        exec(compile(fh.read(), path, "exec"), ns)  # noqa: S102 - pristine source only
    return ns["PC"], ns["SP"], ns["EOS"]


@pytest.fixture(scope="module")
def by_request(report):
    """The run's rows, split per request, in the order they were appended."""
    out = {}
    for row in report["rows"]:
        if not isinstance(row, str):
            pytest.fail("a report row is not a string: %r" % (row,))
        name = row.split(" ", 1)[0]
        out.setdefault(name, []).append(row)
    return out


# ---------------------------------------------------------------- the run happened at all

def test_run_completed_without_error(report):
    assert report["errors"] == [], "the run raised: %s" % "; ".join(report["errors"][:4])


def test_run_saw_every_request(report, specs):
    assert report.get("seen") == len(specs), (
        "the run reports %r requests, %d were generated" % (report.get("seen"), len(specs)))


def test_run_finished_inside_the_stated_limit(report):
    secs = report.get("secs")
    assert isinstance(secs, (int, float)), "the run reported no elapsed time"
    assert secs <= RUN_LIMIT_SECS, (
        "the run took %.1f s against a stated limit of %.0f s" % (secs, RUN_LIMIT_SECS))


# ---------------------------------------------------------------- the rows themselves

def test_enumerated_requests_match_the_sealed_ground_truth(by_request):
    """The enumerated requests, against a ground truth built before the agent existed."""
    with open(os.path.join(HERE, "gt.json"), "r", encoding="utf-8") as fh:
        gt = json.load(fh)
    assert len(gt) == len(cases.CASES), (
        "ground truth holds %d requests, %d are enumerated" % (len(gt), len(cases.CASES)))
    checked = 0
    for name in sorted(gt):
        got = by_request.get(name)
        assert got is not None, "the run emitted nothing for %s" % name
        assert got == gt[name], first_difference(name, gt[name], got)
        checked += 1
    assert checked == len(cases.CASES), "compared %d enumerated requests" % checked


def test_every_request_matches_the_fast_model(by_request, specs, vocab):
    """Every request, enumerated, generated and wide, against the automaton model."""
    pieces, special, eos = vocab
    checked = 0
    for name in sorted(specs):
        want = model.rows(name, specs[name], pieces, special, eos)
        got = by_request.get(name)
        assert got is not None, "the run emitted nothing for %s" % name
        assert got == want, first_difference(name, want, got)
        checked += 1
    assert checked == len(specs), (
        "compared %d requests, %d were generated" % (checked, len(specs)))


def test_narrow_requests_match_the_naive_model(by_request, specs, vocab):
    """The same rows again, against the model that recomputes everything from scratch.

    The wide family is left out on purpose: that model is quadratic, which is the whole
    reason the wide family exists. Every narrow request is checked by both, so the fast
    model is only ever trusted where the naive one has already confirmed it.
    """
    pieces, special, eos = vocab
    checked = 0
    for name in sorted(specs):
        if name.startswith("w"):
            continue
        want = oracle.rows(name, specs[name], pieces, special, eos)
        got = by_request.get(name)
        assert got is not None, "the run emitted nothing for %s" % name
        assert got == want, first_difference(name, want, got)
        checked += 1
    assert checked >= len(cases.CASES) + 300, (
        "only %d narrow requests were checked against the naive model" % checked)


def test_no_request_emitted_rows_it_was_not_asked_for(by_request, specs):
    extra = sorted(set(by_request) - set(specs))
    assert not extra, "the run emitted rows for requests that do not exist: %s" % extra[:4]


def test_each_request_finishes_exactly_once(by_request, specs):
    for name in sorted(specs):
        rows = by_request.get(name, [])
        fins = [r for r in rows if r.split()[1:2] == ["fi"]]
        assert len(fins) == 1, "%s emitted %d finish rows" % (name, len(fins))
        assert rows[-1] == fins[0], "%s emitted rows after finishing" % name


# ---------------------------------------------------------------- evidence of real execution

def test_frozen_entry_points_were_not_rebound(report):
    """Each frozen function, as it stood in the running interpreter, against pristine."""
    marks = report["marks"]
    checked = 0
    for modname, fname in FROZEN:
        key = "%s.%s" % (modname, fname)
        want = pristine_mark(modname, fname)
        assert marks.get(key) == want, (
            "%s was not the pristine function when the run used it" % key)
        checked += 1
    assert checked == len(FROZEN), "checked %d frozen entry points" % checked


def test_executed_tree_matches_pristine_outside_the_declared_artifacts(report):
    """Nothing but the four declared files may differ, and the count is asserted first."""
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

    frozen = sorted(set(want) - set(ARTIFACTS))
    assert len(frozen) >= 8, (
        "expected at least eight frozen files in the pristine tree, found %d" % len(frozen))

    got = report["tree"]
    assert set(got) == set(want), (
        "the executed tree gained or lost files: %s"
        % sorted(set(got).symmetric_difference(want))[:6])

    compared = 0
    for rel in frozen:
        assert got.get(rel) == want[rel], "%s was modified during the run" % rel
        compared += 1
    assert compared == len(frozen), "compared %d frozen files" % compared


def test_the_release_module_ran_for_every_row(report, by_request):
    """The interpreter's own count of entries into the release module.

    The frozen loop asks the release module once per step, so its entry count has to
    account for every `em` row. Rows without entries are rows nobody computed.
    """
    tally = report["tally"]
    for key, value in tally.items():
        assert isinstance(value, int) and value >= 0, "tally %r is not a count" % key
    ems = sum(1 for rows in by_request.values() for r in rows if r.split()[1:2] == ["em"])
    assert ems > 0, "the run emitted no release rows at all"
    seen = tally.get("strm.rel", 0)
    assert seen >= ems, (
        "the release module was entered %d times for %d released rows" % (seen, ems))


# ---------------------------------------------------------------- helpers

def pristine_mark(modname, fname):
    path = os.path.join(PRISTINE, *modname.split(".")) + ".py"
    with open(path, "rb") as fh:
        top = compile(fh.read(), path, "exec")
    code = find_code(top, fname)
    assert code is not None, "no function %s in pristine %s" % (fname, modname)
    h = hashlib.sha256()

    def walk(c):
        h.update(c.co_code)
        h.update(repr(c.co_names).encode("utf-8", "replace"))
        h.update(repr(c.co_varnames).encode("utf-8", "replace"))
        for k in c.co_consts:
            if hasattr(k, "co_code"):
                h.update(b"<code>")
                walk(k)
            else:
                h.update(repr(k).encode("utf-8", "replace"))

    walk(code)
    return h.hexdigest()


def find_code(code, name):
    for const in code.co_consts:
        if hasattr(const, "co_name"):
            if const.co_name == name:
                return const
            found = find_code(const, name)
            if found is not None:
                return found
    return None


def first_difference(name, want, got):
    """A failure that names the step and the rule, rather than dumping two lists."""
    for i in range(max(len(want), len(got))):
        a = want[i] if i < len(want) else "<nothing>"
        b = got[i] if i < len(got) else "<nothing>"
        if a != b:
            return "%s row %d:\n  expected %s\n  emitted  %s" % (name, i, a, b)
    return "%s: %d rows expected, %d emitted" % (name, len(want), len(got))
