"""Verifier for the grant spread order task.

THE VERIFIER CONTRACT, frozen before the environment was finished. It lives here rather
than only in STATE.md because this is the file the run audit and the quality review read,
and STATE.md ships nowhere.

What the run produced is in /work/run/out.json, written by /tests/runner.py, the only
process that executed anything the agent wrote. Nothing in this file imports, execs or
subprocesses agent code. It reads that JSON as hostile input and grades it against
/tests/oracle.py, a sealed second implementation of the same specification sharing no code
with the tree, and against /tests/gt.json, which is root-only and was never visible to the
run.

WHAT IS GRADED, on every journal, exactly, with no partial credit:

  1. THE DECISIONS. Every question the journal asks - a subject, a node, a right - and the
     answer the kernel gave: the verdict, and the identity of the entry that carried it,
     which is the subject it names, the node it was placed on, the sequence number of the
     act that placed it and its scope. Grading the winning entry and not only the verdict
     is deliberate. Two implementations can agree on allow-or-refuse for a reason that has
     nothing to do with the rule under test, and an ordering key that is wrong but rarely
     changes the verdict would be invisible if only the verdict were compared. The winner
     is unique: the three keys are a total order over the candidates, since no two entries
     on one node share an origin, a subject and a right.

  2. THE HOLDINGS. The state of the whole store - every node's parent, whether it is
     accepting inheritance, and the entries it holds with their subject, right, verdict,
     scope, origin and sequence number - digested after every operation and dumped in full
     at the end. The digest is what makes a divergence legible: the grader reports the
     operation index where the two first disagreed, so a failure reads "diverged at
     operation 41: mv n3 n1" rather than as a wall of records.

  Both come out of pol/drv.py, which is not an editable artifact, so they record what the
  kernel actually did rather than what a submission says it did. The digest covers the
  membership table too, which is how "a membership change moves no entries" is graded
  rather than asserted.

TWO JOURNAL SETS, and the second is the reason an answer key is worth nothing:

  The enumerated set in cases.py is thirty journals, one per rule, each named for the
  reading it exists to fail, and including the must-still-work side of every fence. It is
  fixed, it ships in the bundle, and its expected results are in gt.json.

  The differential set is three hundred journals built by gen.py from RUN_NONCE, which
  test.sh makes from /dev/urandom inside this container at trial time. Those journals did
  not exist when the submission was written, and their expected results are produced here
  by the sealed model after the run. There is nothing to hardcode, no table to paste and
  no report to forge: a submission has to implement the rules to answer a journal it has
  never seen. That is what replaces the counter-and-budget accounting the earlier tasks in
  this repo used, and it is strictly stronger, because what is compared is the whole
  behaviour rather than a summary of it.

  On determinism, since a seeded set invites the question: the kernel and the model are
  both deterministic functions of a journal, so a correct submission passes every run with
  certainty and there is no flake being traded for strictness. What the nonce randomises is
  only which journals a WRONG submission is caught by. The reference has been checked
  against the model on several thousand journals across many seeds with no disagreement,
  and build_gt.py refuses to write a ground truth without a clean run.

INTEGRITY, because the verifier executes agent code:

  - The executed tree outside the four declared artifacts must be byte-identical to the
    pristine copy after the run.
  - Every frozen function is fingerprinted as it actually existed in the running
    interpreter, at import and again when each journal finished, against digests derived
    here by compiling the pristine sources - nothing is executed to do it. That catches a
    submission that leaves the files alone and rebinds a function instead.
  - Event rows are accepted by a callable the runner owns, which refuses any caller that
    is not the frozen emitter, so a submission cannot write its own event stream.
  - The interpreter's own count of entries into that emitter must equal the number of rows
    reported, and the instrumentation must still have been registered and armed when each
    journal ended. On 3.12 that count comes from sys.monitoring; on older interpreters from
    the profile hook, and the grader insists on the former when REQUIRE_MONITORING is set.
  - The report must carry the run nonce, so a report planted before the run cannot pass.

DELIBERATELY NOT GRADED, because grading them would measure an implementation choice
rather than behaviour - the run-audit lesson is that a graded quantity two correct
implementations disagree on is a trap and not a test:

  - How often a submission re-flows, how much of a subtree it touches, and whether it
    recomputes a node that did not need it. The hit counts the runner reports are used for
    one thing only, which is that entries into the emitter equal the number of rows. They
    are never compared against a budget.
  - The order in which entries sit inside a node. The holdings are sorted before they are
    digested, so a list-backed store and a set-backed one are indistinguishable.
  - Which data structures a submission keeps, and what it caches between decisions.

  Six alternative correct implementations live in authoring/variants and all six are
  required to score 1: the flow written as a pull instead of a push, the offer materialised
  instead of derived, the decision by a single minimum instead of a sort, the reachability
  walk by depth-first search, the subtree walked breadth-first, and one that keeps its own
  index of origins alongside the store.
"""

import hashlib
import json
import os
import pathlib
import types

import pytest

import cases
import gen
import oracle
from runner import COUNTED, FROZEN, digest, seals

OUT = os.environ.get("RUN_OUT", "/work/run/out.json")
APP = pathlib.Path(os.environ.get("APP_DIR", "/work/app"))
PURE = pathlib.Path(os.environ.get("PRISTINE_DIR", "/pristine"))
STRICT = os.environ.get("REQUIRE_MONITORING", "") not in ("", "0")

EDITABLE = {"pol/spread.py", "pol/weigh.py", "pol/graft.py", "pol/crowd.py"}

ORDER = ("reach-beats-tree", "reach-beats-tree-deep", "placed-here-beats-arrived",
         "later-act-wins", "later-act-wins-reversed", "no-deny-wins-rule",
         "hops-two-loses-to-one", "unreachable-subject-ignored",
         "nothing-matching-refuses", "membership-read-at-decision")

SCOPE = ("down-only-skips-its-node", "down-only-reaches-every-depth",
         "here-only-stays-put", "here-only-replacing-withdraws",
         "scope-rewritten-not-carried", "both-scope-holds")

BAR = ("bar-stops-what-arrives", "bar-stops-the-subtree",
       "bar-keeps-what-it-had-holds", "bar-does-not-stop-a-clear-below-it",
       "planting-on-a-barred-node-holds", "resume-takes-the-chain")

SHAPE = ("move-reflows-the-subtree", "move-drops-what-is-no-longer-above",
         "move-keeps-what-is-still-above-holds", "barred-node-carries-its-snapshot",
         "barred-node-stops-the-reflow", "a-new-node-takes-the-offer",
         "direct-placement-survives-a-move-holds",
         "an-entry-never-returns-to-its-origin")


# --------------------------------------------------------------- reading the report

def load():
    try:
        with open(OUT) as fh:
            blob = json.load(fh)
    except FileNotFoundError:
        pytest.fail("the run produced no report at %s" % OUT)
    except (ValueError, OSError) as exc:
        pytest.fail("the report at %s is unreadable: %s" % (OUT, exc))
    if not isinstance(blob, dict):
        pytest.fail("the report is not an object")
    for field in ("nonce", "count", "done", "broke"):
        if field not in blob:
            pytest.fail("the report has no %r" % field)
    if not isinstance(blob["done"], dict) or not isinstance(blob["broke"], dict):
        pytest.fail("the report's journal tables are not objects")
    return blob


REPORT = load()


def journals():
    named = [(n, cases.PROGS[n]) for n in sorted(cases.PROGS)]
    named += [(n, gen.text(s)) for n, s in gen.batch(REPORT["nonce"], REPORT["count"])]
    return dict(named)


ALL = journals()


def rows_of(name):
    got = REPORT["done"].get(name)
    if got is None:
        if name in REPORT["broke"]:
            pytest.fail("%s raised inside the run:\n%s" % (name, REPORT["broke"][name]))
        pytest.fail("%s is missing from the report" % name)
    if not isinstance(got, dict) or not isinstance(got.get("rows"), list):
        pytest.fail("%s reported no usable rows" % name)
    return [list(r) if isinstance(r, list) else r for r in got["rows"]]


def want(name):
    return [list(r) for r in oracle.rows(ALL[name])]


def blame(name):
    """Return an empty string when the journal matches, or a line naming where it did not."""
    got, exp = rows_of(name), want(name)
    for i, (a, b) in enumerate(zip(got, exp)):
        if a == b:
            continue
        if b and b[0] == "dg":
            step = b[1]
            op = ALL[name].strip().split("\n")[step - 1]
            return ("%s: the holdings diverge at operation %d (%s)"
                    % (name, step, op))
        if b and b[0] == "ak":
            op = ALL[name].strip().split("\n")[b[1] - 1]
            return ("%s: wrong answer at operation %d (%s)\n     got %r\n  wanted %r"
                    % (name, b[1], op, a, b))
        return "%s: row %d\n     got %r\n  wanted %r" % (name, i, a, b)
    if len(got) != len(exp):
        return "%s: %d rows, wanted %d" % (name, len(got), len(exp))
    return ""


def sweep(names):
    bad = [blame(n) for n in names]
    bad = [b for b in bad if b]
    if bad:
        pytest.fail("%d of %d journals wrong\n%s"
                    % (len(bad), len(names), "\n".join(bad[:8])))


# --------------------------------------------------------------- the run happened

def test_the_run_reported_on_these_journals():
    if REPORT["nonce"] != os.environ.get("RUN_NONCE", ""):
        pytest.fail("the report carries nonce %r, this trial made %r - a report that "
                    "predates the run cannot be graded"
                    % (REPORT["nonce"], os.environ.get("RUN_NONCE", "")))
    if REPORT["broke"]:
        first = sorted(REPORT["broke"])[0]
        pytest.fail("%d journals raised inside the run, first %s:\n%s"
                    % (len(REPORT["broke"]), first, REPORT["broke"][first]))
    missing = sorted(set(ALL) - set(REPORT["done"]))
    if missing:
        pytest.fail("%d journals were never reported, first %r"
                    % (len(missing), missing[:5]))


# --------------------------------------------------------------- the rules

def test_which_entry_is_strongest():
    sweep(ORDER)


def test_where_an_entry_applies():
    sweep(SCOPE)


def test_a_node_that_is_not_accepting_inheritance():
    sweep(BAR)


def test_structure_changes_and_the_reflow():
    sweep(SHAPE)


def test_journals_the_submission_has_never_seen():
    sweep([n for n in sorted(ALL) if n not in cases.PROGS])


# --------------------------------------------------------------- the model itself

def test_the_model_still_reproduces_ground_truth():
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gt.json")) as fh:
        book = json.load(fh)
    if sorted(book) != sorted(cases.PROGS):
        pytest.fail("gt.json covers %d cases, cases.py has %d"
                    % (len(book), len(cases.PROGS)))
    for name in sorted(book):
        made = [list(r) for r in oracle.rows(cases.PROGS[name])]
        if made != [list(r) for r in book[name]]:
            pytest.fail("the sealed model no longer reproduces gt.json on %s - the model "
                        "has drifted and every result above is suspect" % name)


# --------------------------------------------------------------- integrity

def walk(root):
    out = {}
    for path in sorted(root.rglob("*")):
        if path.is_dir() or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(root).as_posix()
        out[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def test_only_the_declared_artifacts_changed():
    if not PURE.is_dir():
        pytest.fail("no pristine copy at %s" % PURE)
    here, there = walk(APP), walk(PURE)
    gone = sorted(set(there) - set(here) - EDITABLE)
    extra = sorted(set(here) - set(there))
    moved = sorted(f for f in set(here) & set(there)
                   if f not in EDITABLE and here[f] != there[f])
    if gone or extra or moved:
        pytest.fail("the executed tree is not the shipped one: removed %r, added %r, "
                    "edited outside the declared artifacts %r" % (gone, extra, moved))


def hunt(code, trail):
    for item in code.co_consts:
        if isinstance(item, types.CodeType) and item.co_name == trail[0]:
            return item if len(trail) == 1 else hunt(item, trail[1:])
    return None


def expected():
    book = {}
    for rel, qual in seals():
        src = (PURE / rel).read_text()
        code = hunt(compile(src, rel, "exec"), qual.split("."))
        if code is None:
            pytest.fail("no %s in the pristine %s" % (qual, rel))
        book[rel + "::" + qual] = digest(code)
    acc = hashlib.sha256()
    for tag in sorted(book):
        acc.update(("%s>%s\n" % (tag, book[tag])).encode("utf-8"))
    return acc.hexdigest()


def test_the_frozen_functions_are_the_shipped_ones():
    seal = expected()
    bad = []
    for name in sorted(REPORT["done"]):
        got = REPORT["done"][name]
        if got.get("open") != seal or got.get("shut") != seal:
            bad.append(name)
    if bad:
        pytest.fail("%d journals ran against a kernel that is not the shipped one "
                    "(%d frozen functions checked at import and at the end), first %r"
                    % (len(bad), sum(len(v) for v in FROZEN.values()), bad[:5]))


def test_every_row_came_through_the_emitter():
    bad = []
    for name in sorted(REPORT["done"]):
        got = REPORT["done"][name]
        hits = got.get("hits") or {}
        if not got.get("armed"):
            bad.append("%s: the instrumentation was not armed at the end" % name)
        elif STRICT and got.get("how") != "monitoring":
            bad.append("%s: counted by %r, not by the interpreter" % (name, got.get("how")))
        elif set(hits) != set(COUNTED):
            bad.append("%s: the tally is not the one the runner keeps" % name)
        elif hits.get("ev") != len(got.get("rows") or []):
            bad.append("%s: %d rows reported, the interpreter counted %r emitter entries"
                       % (name, len(got.get("rows") or []), hits.get("ev")))
    if bad:
        pytest.fail("\n".join(bad[:8]))
