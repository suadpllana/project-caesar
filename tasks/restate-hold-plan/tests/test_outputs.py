"""Stage two: grading. Runs as root and never executes a line of the submission.

What is graded, and nothing else
--------------------------------
The printed plan of every graded pipeline, compared line for line and exactly. The planner is
the five collected files `/app/plan/keep.py`, `reach.py`, `look.py`, `settle.py` and
`order.py`, laid by stage one over the verifier's own pristine copy of `/app`, so the driver,
the parser, the time arithmetic and the sample pipelines are ours.

A plan is decided by these rules, each settled the same way by the sealed model
(`seal/model.py`, rules R1-R15) and by the reference in `solution/`, written apart:

  existence   ended by now, and published or now < end + keep; reads before hour 0 drop out
  reach       the corrected partition, and every ended partition of a step whose declared reads
              include a reached one, whether or not the partitions between still exist
  lines       each reached partition of a step that exists: published -> hold pinned; cannot be
              computed -> hold lost; nothing it read changed -> hold same; else a run
  modes       part if anything it read does not agree, else sub if a roll-up stood in, else full
  roll-ups    read in place of a day of hours with a missing hour, only while the roll-up exists
              and agrees, never for its own computation
  temps       a missing partition is computed once from its own reads; a missing source partition
              cannot be; a temp line exists only for what a run or a printed temp read
  order       runs and temps after what they read, earliest end then earliest declared; the
              holds last, by end and then declaration

Implementation choice, and not graded: how any of it is stored, whether partitions are settled
recursively or in time order, how the order is computed, and every internal name. Not free, and
not asserted here: the whole set has to finish inside the 60 second clock that stage one runs
under, which is what makes walking every partition from hour 0 fail.

Enumerated pipelines are checked against `seal/gt.json`, frozen from the model after each plan
was derived by hand. Generated pipelines are drawn from a seed made after the agent finished and
checked against the model, which must first reproduce `gt.json` itself.
"""
import hashlib
import json
import os
import sys

import pytest

import cases
import gen

SEAL = os.environ.get("RHP_SEAL", "/tests/seal")
WORK = os.environ.get("RHP_WORK", "/work")
LOGS = os.environ.get("RHP_LOGS", "/logs/verifier")
sys.path.insert(0, SEAL)

import model  # noqa: E402


def digest(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def plan_of(record):
    """The plan inside one record from stage one, which is treated as hostile."""
    if not isinstance(record, dict):
        pytest.fail("a record from stage one is not an object")
    if "plan" not in record:
        pytest.fail("the planner raised on %s: %s" % (record.get("name"), record.get("error")))
    plan = record["plan"]
    if not isinstance(plan, list) or not all(isinstance(line, str) for line in plan):
        pytest.fail("the plan for %s is not a list of lines" % record.get("name"))
    return plan


@pytest.fixture(scope="module")
def planned():
    try:
        with open(os.path.join(WORK, "planned.json"), encoding="utf-8") as fh:
            raw = json.load(fh)
    except Exception as exc:
        pytest.fail("stage one left no readable record: %s" % exc)
    if not isinstance(raw, list):
        pytest.fail("the record from stage one is not a list")
    by_name = {}
    for record in raw:
        if not isinstance(record, dict) or not isinstance(record.get("name"), str):
            pytest.fail("a record from stage one has no name")
        by_name[record["name"]] = record
    return by_name


@pytest.fixture(scope="module")
def frozen():
    with open(os.path.join(SEAL, "gt.json"), encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def population():
    with open(os.path.join(LOGS, "seed"), encoding="utf-8") as fh:
        seed = fh.read().strip()
    with open(os.path.join(LOGS, "each"), encoding="utf-8") as fh:
        each = int(fh.read().strip())
    return gen.programs(seed, each)


# --- the sealed side must agree with itself before it judges anyone --------------------

def test_model_reproduces_the_frozen_plans(frozen):
    assert sorted(frozen) == sorted(cases.ORDER)
    for name in cases.ORDER:
        assert model.expect(cases.prog(name)) == frozen[name], name


# --- the enumerated pipelines, each named for the rule it pins ---------------------------

@pytest.mark.parametrize("name", cases.ORDER)
def test_enumerated_plan(planned, frozen, name):
    assert name in planned, "no plan was recorded for %s" % name
    record = planned[name]
    assert record.get("digest") == digest(cases.prog(name)), "the pipeline was altered"
    assert plan_of(record) == frozen[name]


# --- the generated pipelines, drawn after the agent was gone -----------------------------

def test_population_covers_every_family(population):
    assert {family for family, _name, _lines in population} == {f for f, _big in gen.FAMILIES}
    assert len(population) >= 400


def test_every_generated_plan(planned, population):
    wrong = []
    for _family, name, lines in population:
        record = planned.get(name)
        if record is None:
            wrong.append((name, "no plan recorded"))
        elif record.get("digest") != digest(lines):
            wrong.append((name, "the pipeline was altered"))
        elif plan_of(record) != model.expect(lines):
            wrong.append((name, "the plan differs"))
    assert not wrong, "%d of %d generated plans are wrong, first: %s" % (
        len(wrong), len(population), wrong[:3])
