"""Half two of grading: the verdict.

The frozen contract, in one place.

  Collected        /app/rng/seg.py, pick.py, hole.py, knit.py, age.py, ask.py. Nothing else
                   is read from the agent's container. The six are laid over the verifier's
                   own pristine copy of the tree, so the driver, the store, the program
                   parser and the trace writer are always the shipped ones.
  Graded           the whole stdout trace of every graded program, line for line, exactly.
                   31 enumerated programs against answers frozen before this file was
                   written, and 364 generated programs against the sealed model.
  Tolerances       none. Lines are compared as strings.
  Limit            60 seconds of wall clock on the stage that runs submitted code, enforced
                   in test.sh, validated against two independently written correct engines.
  Ground truth     tests/seal/gt.json and tests/seal/model.py, in a root-owned directory at
                   mode 0700 from before the first submitted line ran.

Nothing here takes the worker's word for anything. The program list is rebuilt from the
root-owned seed, every record is matched to a program by name, and the digest of the text the
worker says it ran is recomputed here and compared - a record for a program the grader did not
ask for, or for a shorter version of one it did, fails.
"""

import hashlib
import json
import pathlib
import sys

sys.path.insert(0, "/tests")
sys.path.insert(0, "/tests/seal")

import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

PAID = pathlib.Path("/logs/verifier")
SAID = pathlib.Path("/work/said.json")
SEAL = pathlib.Path("/tests/seal/gt.json")


def _jobs():
    seed = (PAID / "nonce").read_text(encoding="utf-8").strip()
    per = int((PAID / "per").read_text(encoding="utf-8").strip())
    out = [("hand", name, cases.prog(name)) for name in cases.ORDER]
    out += gen.programs(seed, per)
    return out


def _record():
    """The worker's output, read defensively: every field may be anything at all."""
    if not SAID.is_file():
        return None
    try:
        rows = json.loads(SAID.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(rows, list):
        return None
    kept = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = row.get("name")
        if isinstance(name, str) and name not in kept:
            kept[name] = row
    return kept


JOBS = _jobs()
ROWS = _record()
TRUTH = json.loads(SEAL.read_text(encoding="utf-8"))


def _said(row):
    """The trace the worker recorded, or None if it is not a list of strings."""
    said = row.get("said")
    if not isinstance(said, list):
        return None
    for line in said:
        if not isinstance(line, str):
            return None
    return said


def test_record_is_complete():
    """Every graded program was run, on the text the grader asked for."""
    assert ROWS is not None, "half one left no readable record of what it ran"
    missing = [name for _, name, _ in JOBS if name not in ROWS]
    assert not missing, "no record for %d programs, first %s" % (len(missing), missing[:4])
    for fam, name, lines in JOBS:
        text = "\n".join(lines) + "\n"
        want = hashlib.sha256(text.encode("utf-8")).hexdigest()
        assert ROWS[name].get("seal") == want, \
            "%s was run on different text from the one it was set" % name


def test_nothing_raised():
    """A program that threw is a failure, whatever the rest of the run did."""
    assert ROWS is not None, "half one left no readable record of what it ran"
    blew = [(name, ROWS[name].get("blew")) for _, name, _ in JOBS
            if name in ROWS and ROWS[name].get("blew")]
    assert not blew, "%d programs raised, first %r" % (len(blew), blew[:2])


def test_enumerated_programs():
    """The 31 named programs match answers frozen before this file existed.

    Each name says which rule it pins - the version a read is served at, what a commit does
    to a stretch, what a fetch is correct from, the horizon, the order and shape of the
    answer - so a failure reports the decision rather than a program number.
    """
    assert ROWS is not None, "half one left no readable record of what it ran"
    wrong = []
    for name in cases.ORDER:
        want = TRUTH[name]
        got = _said(ROWS.get(name, {}))
        if got != want:
            wrong.append(name)
    assert not wrong, "%d of %d enumerated programs wrong: %s" \
        % (len(wrong), len(cases.ORDER), ", ".join(wrong[:8]))


def test_model_still_matches_the_frozen_answers():
    """The sealed model is held to the same frozen answers the submission is."""
    drift = [name for name in cases.ORDER
             if model.trace("\n".join(cases.prog(name)) + "\n") != TRUTH[name]]
    assert not drift, "the sealed model no longer reproduces %s" % drift[:4]


def test_generated_programs():
    """Every generated program matches the sealed model, line for line.

    The seed was drawn after the agent's container was gone, so these programs did not exist
    while the submission was being written. The families are shaped at the decisions rather
    than sampled uniformly, and two of them are sized so that a correct cache which searches
    the allowance version by version does not finish inside the limit.
    """
    assert ROWS is not None, "half one left no readable record of what it ran"
    wrong = []
    for fam, name, lines in JOBS:
        if fam == "hand":
            continue
        want = model.trace("\n".join(lines) + "\n")
        got = _said(ROWS.get(name, {}))
        if got != want:
            where = "?"
            if isinstance(got, list):
                for i, (a, b) in enumerate(zip(got, want)):
                    if a != b:
                        where = "line %d, got %r want %r" % (i, a, b)
                        break
                else:
                    where = "%d lines against %d" % (len(got), len(want))
            wrong.append("%s (%s)" % (name, where))
    assert not wrong, "%d generated programs wrong, first: %s" % (len(wrong), wrong[:2])
