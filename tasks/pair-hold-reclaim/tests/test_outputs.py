"""The grader.

Runs as root after the sandboxed run has finished and been reaped, reads the run's
report as hostile input, and never executes anything the submission wrote.

THE CONTRACT, frozen before the environment was written.

What is graded, exactly and with no partial credit:

  the ledger      Every row, in order, for every stream: which cleanup ran, which watch
                  was emptied, which entry was dropped, which cell was let go, and what
                  each read of a watch answered. The rows are appended inside core/st.py,
                  which is not a declared artifact, so they record what the store was
                  actually made to do rather than what a submission says it did.

  the final state The cells still present with their links, the entry tables, what each
                  watch names, and the bound names. This is a cross-check on the ledger
                  rather than a second axis: the store removes a cell in the same call
                  that records the row, so the two can only disagree if a submission
                  reached past the store's own methods.

Which streams:

  enumerated      The streams in tests/scen.py, one per rule, each named for the reading
                  it exists to fail, including the must-still-work side of every fence.
                  Their expected answers are in tests/gt.json, and the sealed model in
                  tests/oracle.py re-derives them here, so a ground truth that has
                  drifted from the specification fails the run rather than passing it.

  generated       Three hundred streams built inside this container from a nonce made
                  out of /dev/urandom at trial time, after the submission was written.
                  Their expected answers come from the sealed model after the run. There
                  is nothing here to paste: the streams did not exist when the
                  submission did.

What is deliberately NOT graded, because grading it would measure an arrangement of the
code rather than the behaviour the rules describe: how many times a submission marks,
what it caches between rounds, which data structures it keeps, and how many rounds it
takes to settle. Six alternative correct implementations live in authoring/variants and
all six are required to score 1.

Since the run executes agent code, four attestations are graded alongside the answers:
the executed tree outside the four declared artifacts must be byte-identical to the
pristine copy; every sealed function must still be the one compiled from those sources;
the ledger sink must have refused every caller that was not the store, and the
interpreter's own tally of entries into the store's recording methods must be at least
as large as the rows those methods produced and must still have been armed at the end;
and the report must carry the nonce this container made.
"""

import hashlib
import json
import os
import pathlib

import pytest

import gen
import oracle
import scen

REPORT = pathlib.Path(os.environ.get("PHR_REPORT", "/rep/out.json"))
PRISTINE = pathlib.Path("/pristine")
GT = pathlib.Path("/tests/gt.json")
NONCE_FILE = pathlib.Path("/tests/nonce")
ARTIFACTS = ("rch.py", "cln.py", "pss.py", "obs.py")
SEALED = {
    "st.Store.wipe": ("core/st.py", ("Store", "wipe")),
    "st.Store.fire": ("core/st.py", ("Store", "fire")),
    "st.Store.letgo": ("core/st.py", ("Store", "letgo")),
    "st.Store.look": ("core/st.py", ("Store", "look")),
    "st.Store.mk": ("core/st.py", ("Store", "mk")),
    "ex.apply": ("core/ex.py", ("apply",)),
    "rd.parse": ("core/rd.py", ("parse",)),
}
ROWS = {"em": "Store.wipe", "cn": "Store.fire", "rl": "Store.letgo", "sh": "Store.look"}


def _load():
    try:
        body = REPORT.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        pytest.fail("the run left no report at %s (%s)" % (REPORT, exc))
    if not body.strip():
        pytest.fail("the run left an empty report at %s: it did not finish" % REPORT)
    try:
        data = json.loads(body)
    except ValueError as exc:
        pytest.fail("the report is not JSON (%s); first 200 bytes: %r" % (exc, body[:200]))
    if not isinstance(data, dict):
        pytest.fail("the report is a %s, not an object" % type(data).__name__)
    return data


def _runs(data):
    runs = data.get("runs")
    return runs if isinstance(runs, dict) else {}


@pytest.fixture(scope="module")
def report():
    return _load()


@pytest.fixture(scope="module")
def expected(report):
    nonce = report.get("nonce")
    streams = scen.cases() + gen.build(nonce, int(report.get("count") or 0))
    return {name: oracle.play(text) for name, text in streams}, streams


def _walk_code(code, path):
    """Find a nested code object by name, so a digest can be taken from source."""
    head, rest = path[0], path[1:]
    for const in code.co_consts:
        if hasattr(const, "co_code") and const.co_name == head:
            return _walk_code(const, rest) if rest else const
    return None


def _print_of_code(code):
    flat = [repr(x) for x in code.co_consts if not hasattr(x, "co_code")]
    blob = b"|".join([code.co_code, repr(code.co_names).encode(),
                      repr(code.co_varnames).encode(), repr(flat).encode()])
    return hashlib.sha256(blob).hexdigest()[:32]


def _pristine_digest():
    parts = []
    for base, dirs, files in os.walk(PRISTINE):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for f in sorted(files):
            rel = os.path.relpath(os.path.join(base, f), PRISTINE)
            if rel.startswith("core/") and os.path.basename(rel) in ARTIFACTS:
                continue
            if f.endswith(".pyc"):
                continue
            parts.append(rel + ":" + hashlib.sha256(
                (PRISTINE / rel).read_bytes()).hexdigest())
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def test_the_run_produced_a_report(report):
    assert report.get("fault") is None, (
        "the run raised before it could finish:\n%s" % report.get("fault"))
    assert _runs(report), "the report carries no stream results at all"


def test_the_report_carries_this_container_s_nonce(report):
    want = NONCE_FILE.read_text(encoding="utf-8").strip()
    assert report.get("nonce") == want, (
        "the report's nonce is %r and this container made %r, so the report was not "
        "written by this run" % (report.get("nonce"), want))


def test_the_executed_tree_was_the_shipped_one(report):
    assert report.get("digest") == _pristine_digest(), (
        "the executed tree differs from the pristine copy outside the four declared "
        "artifacts")


def test_every_sealed_function_was_the_one_we_shipped(report):
    prints = report.get("prints") or {}
    for name, (rel, path) in sorted(SEALED.items()):
        code = compile((PRISTINE / rel).read_text(encoding="utf-8"), rel, "exec")
        want = _print_of_code(_walk_code(code, path))
        assert prints.get(name) == want, (
            "%s was not the function compiled from the shipped %s when the run started"
            % (name, rel))
    assert not report.get("prints_drifted"), (
        "a sealed function was rebound part way through the run: %s"
        % report.get("prints_drifted"))


def test_the_recording_methods_were_watched_throughout(report):
    assert report.get("armed") is True, (
        "the interpreter instrumentation was not still armed when the last stream ended "
        "(mode %r)" % report.get("mode"))
    tally = report.get("tally") or {}
    seen = {}
    for entry in _runs(report).values():
        for row in entry.get("log") or []:
            code = row.split()[1] if len(row.split()) > 1 else ""
            if code in ROWS:
                seen[ROWS[code]] = seen.get(ROWS[code], 0) + 1
    for name, count in sorted(seen.items()):
        assert tally.get(name, 0) >= count, (
            "%d rows came from %s but the interpreter counted only %d entries into it"
            % (count, name, tally.get(name, 0)))


def test_the_ground_truth_still_matches_the_specification(expected):
    want, _ = expected
    stored = json.loads(GT.read_text(encoding="utf-8"))
    for name, _text in scen.cases():
        assert stored[name]["log"] == want[name]["log"], (
            "tests/gt.json and the sealed model disagree on %s" % name)
        assert stored[name]["state"] == want[name]["state"], (
            "tests/gt.json and the sealed model disagree on the final state of %s" % name)
        blob = "\n".join(stored[name]["log"] + ["--"] + stored[name]["state"]).encode()
        assert stored[name]["digest"] == hashlib.sha256(blob).hexdigest(), (
            "the stored digest for %s does not cover the rows beside it, so gt.json has "
            "been edited by hand rather than regenerated" % name)


def _compare(report, expected, names, label):
    want, _ = expected
    runs = _runs(report)
    misses = []
    for name in names:
        got = runs.get(name)
        if not isinstance(got, dict):
            misses.append("%s: the run reported nothing" % name)
            continue
        if got.get("err"):
            misses.append("%s: the run raised %s" % (name, got["err"]))
            continue
        if got.get("log") != want[name]["log"]:
            misses.append("%s: %s" % (name, _first_diff(got.get("log") or [],
                                                        want[name]["log"])))
        elif got.get("state") != want[name]["state"]:
            misses.append("%s: final state %r, expected %r"
                          % (name, got.get("state"), want[name]["state"]))
    assert not misses, "%d of %d %s streams are wrong:\n  %s" % (
        len(misses), len(names), label, "\n  ".join(misses[:12]))


def _first_diff(got, want):
    for n in range(max(len(got), len(want))):
        a = got[n] if n < len(got) else "(nothing)"
        b = want[n] if n < len(want) else "(nothing)"
        if a != b:
            return "row %d is %r, expected %r" % (n, a, b)
    return "identical"


def test_the_enumerated_streams(report, expected):
    _compare(report, expected, [n for n, _ in scen.cases()], "enumerated")


def test_the_generated_streams(report, expected):
    _, streams = expected
    named = [n for n, _ in streams if n.startswith("g")]
    assert len(named) >= 100, "only %d generated streams were driven" % len(named)
    _compare(report, expected, named, "generated")
