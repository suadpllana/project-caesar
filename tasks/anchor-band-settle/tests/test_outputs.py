"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the four files under `/app/view/`: `lay.py` lays the tree out, `stick.py`
decides which headers are stuck and how far down the view they reach, `pick.py` chooses the box
the view is held by, and `hold.py` settles each frame. Everything else in the tree is the
verifier's own pristine copy - the grammar, the tree and its edits, the frame driver and the
line it prints - so only those four can change what a program prints.

Each frame prints `<n> <offset> <word>`: the frame's number from 1, the scroll offset after the
frame, and the id of the box the view was held by, or `off scroll`, `off live` or `none`.
Graded, and settled the same way by two implementations written apart:

  1  flow: a box's height is its own height plus its children's unless it is shut; a lifted
     box and everything in it take no space; tops follow document order
  2  sticking: a pinned box that is laid out and has height sticks at offset s when the lesser
     of s plus its inset and the end of its section less its height is greater than its top,
     and is drawn there
  3  the band: the lowest bottom edge of the stuck boxes below the top of the view, never less
     than zero
  4  the pick region: the part of the view below the band, empty when the band reaches the
     bottom of the view; a box shows when some of it lies there
  5  the pick walk: document order; lifted, live and zero-height boxes skipped with everything
     inside them; a box wholly in the region is taken; a box partly in it is looked into and
     taken itself when nothing inside it is; a shut box is not looked into
  6  the chain: the holder and every box above it, each with its distance from the band line
     as the tree stood before the edits
  7  qualifying: in the tree, laid out, of some height, and neither it nor any box above it
     stuck at the offset the pass began from - judged again on every pass
  8  falling back: the first box of the chain that qualifies holds the pass, at its own
     distance; when none does the frame ends at the offset that pass began from, clamped, `none`
  9  the target: the holder's top, less its distance, less the band read at the offset the pass
     began from, clamped into the scroll range of the tree after the edits
 10  settling: the first pass starts at the old offset; a pass that does not move the view ends
     the frame; after four passes the smallest offset any of them produced, held by the first
     pass that produced it
 11  the scroll switch: an explicit scroll ends holding for the frame; the last one counts,
     clamped to the tree after the edits; `off scroll`
 12  the live switch: an edit naming a box that is live or inside a live box ends holding for
     the frame, which keeps its old offset clamped; `off live`; a scroll outranks it
 13  nothing picked before the edits: the old offset clamped, `none`

Implementation choice, and not graded: how heights, tops and the stuck set are cached or
recomputed, which module does what, and any internal naming. Not a free choice, and not
asserted in this file either: a full relayout of the tree per frame cannot get the scale
programs through the worker's wall clock, which test.sh sets and the brief states.

Hand cases are checked against seal/gt.json, frozen before this file was written. Generated
programs come from a seed drawn after the agent had finished, and are checked against the
sealed model. The model must also reproduce gt.json exactly, so a drifted model cannot quietly
redefine correct.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

import cases

SEAL = os.environ.get("ABS_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("ABS_WORK", "/work"))
RUN = pathlib.Path(os.environ.get("ABS_RUN", "/tests/run"))
LOGS = pathlib.Path(os.environ.get("ABS_LOGS", "/logs/verifier"))
OUT = WORK / "worker_out.json"
PROGS = RUN / "progs.json"
GT = pathlib.Path(SEAL) / "gt.json"
SMALL_FAMILIES = {"plain", "band", "stick", "cycle", "push", "fall", "turn", "clamp", "switch",
                  "top", "edge", "mix", "rare"}
BIG_FAMILIES = {"long", "wide"}


def _sig(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@pytest.fixture(scope="module")
def programs():
    """The graded programs, from the root-owned file whose hash root took before half one."""
    raw = PROGS.read_bytes()
    want = (LOGS / "progs.sha").read_text(encoding="utf-8").strip()
    assert hashlib.sha256(raw).hexdigest() == want, "the program file changed after it was written"
    return json.loads(raw.decode("utf-8"))


@pytest.fixture(scope="module")
def produced():
    """Every byte here came from a process that ran agent code. Parse it defensively."""
    try:
        raw = json.loads(OUT.read_text(encoding="utf-8"))
    except Exception as exc:
        pytest.fail("worker produced no readable output: %s" % exc)
    if not isinstance(raw, list):
        pytest.fail("worker output is not a list")
    by = {}
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            pytest.fail("worker output entry is malformed")
        by[item["name"]] = item
    return by


@pytest.fixture(scope="module")
def truth():
    return json.loads(GT.read_text(encoding="utf-8"))


def _lines(item):
    got = item.get("got")
    if got is None:
        pytest.fail("the program raised or printed nothing: %s" % (item.get("err"),))
    if not isinstance(got, list) or not all(isinstance(x, str) for x in got):
        pytest.fail("the record is not a list of lines")
    return got


# --- the sealed side has to agree with itself before it judges anything ------------------

def test_frozen_truth_matches_the_model(truth):
    """gt.json was frozen from the model. If they have drifted apart, grade nothing."""
    assert sorted(truth) == sorted(cases.ORDER)
    for name in cases.ORDER:
        assert model.expect(cases.prog(name)) == truth[name], name


def test_program_file_holds_every_family(programs):
    """The worker was given the enumerated programs and every generated family."""
    fams = {p["fam"] for p in programs}
    assert fams == SMALL_FAMILIES | BIG_FAMILIES | {"hand"}
    hand = [p["name"] for p in programs if p["fam"] == "hand"]
    assert hand == list(cases.ORDER)
    assert len([p for p in programs if p["fam"] in SMALL_FAMILIES]) >= 300


# --- the enumerated programs: one per graded decision, and both sides of each fence ------

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_case(produced, truth, name):
    assert name in produced, "no result for hand case %s" % name
    item = produced[name]
    text = "\n".join(cases.prog(name)) + "\n"
    assert item.get("sig") == _sig(text), "hand program was altered: %s" % name
    assert _lines(item) == truth[name]


# --- programs generated from a seed drawn after the agent's container was gone ------------

def test_every_small_program_matches(programs, produced):
    bad = []
    mine = [p for p in programs if p["fam"] in SMALL_FAMILIES]
    for p in mine:
        item = produced.get(p["name"])
        if item is None:
            bad.append((p["name"], "missing"))
        elif item.get("sig") != _sig(p["text"]):
            bad.append((p["name"], "program altered"))
        elif item.get("got") != model.expect(p["text"].splitlines()):
            bad.append((p["name"], "lines differ"))
    assert not bad, "%d of %d generated programs wrong, first: %s" % (len(bad), len(mine), bad[:4])


@pytest.mark.parametrize("fam", sorted(BIG_FAMILIES))
def test_every_scale_program_matches(programs, produced, fam):
    bad = []
    mine = [p for p in programs if p["fam"] == fam]
    assert mine, "no %s programs were generated" % fam
    for p in mine:
        item = produced.get(p["name"])
        if item is None:
            bad.append((p["name"], "missing"))
        elif item.get("sig") != _sig(p["text"]):
            bad.append((p["name"], "program altered"))
        elif item.get("got") != model.expect(p["text"].splitlines()):
            bad.append((p["name"], "lines differ"))
    assert not bad, "%d of %d %s programs wrong: %s" % (len(bad), len(mine), fam, bad[:4])
