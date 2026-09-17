"""Stage two: grade the record stage one left behind. Root, and it runs no agent code.

FROZEN CONTRACT
---------------
`/app/hb/` supplies six files and nothing else is read: `book.py` records what each job holds,
`fit.py` decides what conflicts and what a job already covers, `line.py` keeps the waiting
requests, `lift.py` turns a slot request into a request for the box, `snarl.py` finds the jobs
that have come to wait for each other, and `door.py` drives take, drop and end. The rest of the
tree is this container's own copy, so those six are the only thing that can move a trace.

Thirteen decisions are graded, and two implementations written apart settle them the same way:

  1  a claim on a box and a claim on any of its slots conflict when at least one is w
  2  sibling slots never conflict, two readers never conflict, and a job never blocks itself
  3  a request is granted ahead of the line when the job already covers it on that node or on
     its box, and a claim on a slot covers nothing above it
  4  a hold is a list of acquires: a drop takes back the most recent and what is left decides
  5  a blocked request waits, and so does one behind an older conflicting request
  6  grants come out in one sequence taken across the store, not one per node
  7  a slot request lifts at four distinct slots of a box, in w if the request or any of them is
  8  a lifted request that cannot be granted waits, holding its slot claims until it is
  9  a granted lift frees those claims in slot order and then grants what caused it
 10  the waits-for relation runs through older waiting requests as well as granted claims, and
     the job stopped is the one on a cycle with the fewest acquires, ties to the largest number
 11  a job acts on no line while its own request waits, after it ends, or after it is stopped
 12  end frees in node order and then says done
 13  show lists holders by job number with their acquires as sorted letters

Not graded, and deliberately: how the six divide the work, how holdings are indexed, whether the
line is one structure or one per box, and how the cycle is found. Not free either, and not
asserted here: none of the three questions above can be answered by walking the whole store and
still finish inside the clock stage one runs under.

The enumerated programs are checked against `seal/gt.json`, frozen before this file existed. The
generated ones are checked against `seal/twin.py`, which is also made to reproduce `gt.json`
before it is allowed to judge anything.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

import cases
import gen

SEAL = pathlib.Path(os.environ.get("CCL_SEAL", "/tests/seal"))
sys.path.insert(0, str(SEAL))

import twin  # noqa: E402

YARD = pathlib.Path(os.environ.get("CCL_WORK", "/work"))
LOGS = pathlib.Path(os.environ.get("CCL_LOGS", "/logs/verifier"))


def mark(body):
    return hashlib.blake2s("\x1f".join(body).encode("utf-8")).hexdigest()


class Record:
    """Stage one's output, read as hostile input: every shape is checked before it is used."""

    def __init__(self, blob):
        if not isinstance(blob, dict):
            pytest.fail("the record is not an object")
        self.ran = blob.get("ran")
        self.broke = blob.get("broke")
        if not isinstance(self.ran, dict) or not isinstance(self.broke, dict):
            pytest.fail("the record has no ran and broke tables")

    @classmethod
    def load(cls):
        try:
            return cls(json.loads((YARD / "bench_out.json").read_text(encoding="utf-8")))
        except (OSError, ValueError) as exc:
            pytest.fail("stage one left no readable record: %s" % exc)

    def trace(self, name, body):
        if name in self.broke:
            pytest.fail("the service raised on %s: %s" % (name, self.broke[name]))
        got = self.ran.get(name)
        if not isinstance(got, dict):
            pytest.fail("no record for %s" % name)
        if got.get("sig") != mark(body):
            pytest.fail("the program %s was not the one that ran" % name)
        out = got.get("out")
        if not isinstance(out, list) or not all(isinstance(one, str) for one in out):
            pytest.fail("the trace of %s is not a list of lines" % name)
        return out


@pytest.fixture(scope="module")
def record():
    return Record.load()


@pytest.fixture(scope="module")
def frozen():
    return json.loads((SEAL / "gt.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def exam():
    seed = (LOGS / "nonce").read_text(encoding="utf-8").strip()
    return gen.programs(seed, int((LOGS / "per").read_text(encoding="utf-8").strip()))


# --- the sealed side has to agree with itself before it judges anything ----------------

def test_the_twin_still_makes_the_frozen_answers(frozen):
    """gt.json came from the twin. Drifted apart, they would grade nothing between them."""
    assert sorted(frozen) == sorted(cases.ORDER)
    for name in cases.ORDER:
        assert twin.expect(cases.ops(name)) == frozen[name], name


# --- one enumerated program per graded decision, and per must-still-work fence ---------

@pytest.mark.parametrize("name", cases.ORDER)
def test_enumerated_program(record, frozen, name):
    assert record.trace(name, cases.ops(name)) == frozen[name]


# --- and the population drawn from a seed taken after the agent's container was gone ---

def test_generated_program(record, exam):
    assert len(exam) >= 300, "the generated population came out at %d" % len(exam)
    wrong = []
    for _family, name, body in exam:
        if name in record.broke:
            wrong.append((name, "raised"))
            continue
        got = record.ran.get(name)
        if not isinstance(got, dict) or got.get("sig") != mark(body):
            wrong.append((name, "missing or altered"))
            continue
        if got.get("out") != twin.expect(body):
            wrong.append((name, "trace differs"))
    assert not wrong, "%d of %d generated programs wrong, first: %s" % (
        len(wrong), len(exam), wrong[:4])


def test_every_family_was_run(record, exam):
    """A shrunken exam is a failed one: every family the grader asked for has to be there."""
    assert {family for family, _n, _b in exam} == {name for name, _big in gen.FAMILIES}
    assert set(record.ran) | set(record.broke) >= {name for _f, name, _b in exam}
