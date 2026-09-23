"""The judge. Runs as root and imports nothing the submission wrote.

FROZEN CONTRACT
---------------
Six files under `/app/sim/` come from the agent: the cache of one multiprocessor (`line.py`),
global memory with the caches over it (`mem.py`), block placement (`place.py`), a
multiprocessor's issue rotation (`turn.py`), one instruction (`step.py`) and the launch clock
(`clock.py`). The parser, the printer and the runner are this verifier's pristine copies, so
nothing but those six decides what a launch prints.

What is graded, each settled identically by the sealed model and by a plain cycle stepper
written apart from it:

  1  placement: the lowest-numbered unplaced block goes to the multiprocessor with the most
     free slots, ties to the lower number, into its lowest free slot; an exit frees its slot
     from the next cycle, and a block placed at a cycle issues in that cycle
  2  rotation: one instruction per multiprocessor per cycle, from the first ready block in slot
     order after the slot that issued last; multiprocessors go in number order and every
     effect is complete before the next issue
  3  work: a block that issues `work v` at t is ready again at t + max(1, v)
  4  a cached load fills a four-word line as memory holds it at that moment and is answered
     from the line until it goes; a full cache drops the line filled earliest
  5  a bypassing load answers from memory and drops the line from its own cache only
  6  a store writes memory and the storer's own cached copy, and never fills a line
  7  an atomic works on memory and leaves every cache as it was
  8  a fence empties the issuer's own cache
  9  a spin makes one attempt per issue, loaded value on the left of its comparison, and takes
     its turn like any other instruction
 10  a cache belongs to its multiprocessor for the whole launch
 11  a hang is the first cycle from which every placed block that has not exited sits at a
     spin, none is busy, and no attempt succeeds again; the stuck blocks and the number never
     placed are reported with it
 12  a sum takes n issues of its block, one line per issue from the line holding its address
     upward; each issue reads its line the way the matching load would - the cached copy or a
     fill for sum.ca, memory and a drop of its own cached copy for sum.cg - and adds the four
     words, and the n-th issue writes the total to rd; a block at a sum is ready, takes its
     turn, and is not at a spin

Left to the submission: how caches, rotations and blocks are held, whether the clock steps or
jumps, how a hang is recognised. The one constraint on those choices is time, and it is the
run stage's clock in test.sh that enforces it, not an assertion here: stepping every cycle in
which a block spins cannot get through the two older large families, and neither stepping
every sum issue nor carrying every multiprocessor forward at every event anywhere on the device
gets through the streaming one.

The hand answers in gt.json were frozen from the sealed model, and the first test re-derives
every one of them, so a model that drifted cannot redefine correct without failing here first.
Generated launches come from a seed drawn after the agent's container was gone and are judged
against the model directly.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

import cases
import gen

SEALED = Path(os.environ.get("SLS_SEAL", "/tests/seal"))
sys.path.insert(0, str(SEALED))

import model  # noqa: E402

RECORDS = Path(os.environ.get("SLS_WORK", "/work")) / "worker_out.json"
VERDICT = Path(os.environ.get("SLS_LOGS", "/logs/verifier"))


def digest(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


class Records:
    """What the run stage wrote, read as hostile input: one entry per launch name."""

    def __init__(self, path):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            pytest.fail("the run stage left no readable record: %s" % exc)
        if not isinstance(raw, list):
            pytest.fail("the record is not a list")
        self.by_name = {}
        for entry in raw:
            if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
                pytest.fail("a record entry is malformed")
            self.by_name[entry["name"]] = entry

    def printed(self, name, lines):
        """The lines launch `name` printed, or None and the reason there are none to judge."""
        entry = self.by_name.get(name)
        if entry is None:
            return None, "missing"
        if entry.get("sig") != digest(lines):
            return None, "the launch it ran was not the launch it was given"
        got = entry.get("got")
        if not isinstance(got, list) or not all(isinstance(x, str) for x in got):
            return None, "raised or printed nothing: %s" % (entry.get("err"),)
        return got, None


@pytest.fixture(scope="module")
def records():
    return Records(RECORDS)


@pytest.fixture(scope="module")
def frozen():
    return json.loads((SEALED / "gt.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def drawn():
    seed = (VERDICT / "nonce").read_text(encoding="utf-8").strip()
    per = int((VERDICT / "per").read_text(encoding="utf-8").strip())
    return gen.programs(seed, per)


def test_frozen_answers_are_the_models(frozen):
    """If gt.json and the sealed model disagree the judge itself is broken: grade nothing."""
    assert sorted(frozen) == sorted(cases.ORDER)
    for name in cases.ORDER:
        assert model.expect(cases.prog(name)) == frozen[name], name


@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_launch(records, frozen, name):
    got, why = records.printed(name, cases.prog(name))
    assert why is None, "%s: %s" % (name, why)
    assert got == frozen[name]


def test_generated_launches(records, drawn):
    assert len(drawn) >= 300, "generated set too small: %d" % len(drawn)
    wrong = []
    for _fam, name, lines in drawn:
        got, why = records.printed(name, lines)
        if why is None and got != model.expect(lines):
            why = "lines differ"
        if why is not None:
            wrong.append((name, why))
    assert not wrong, "%d of %d generated launches wrong, first: %s" % (
        len(wrong), len(drawn), wrong[:4])


def test_generated_set_covers_every_family(drawn):
    assert {fam for fam, _n, _l in drawn} == {fam for fam, _big in gen.FAMILIES}
