"""Verifier for the turn seam alignment task.

What the run produced is in /work/out.json, written by /driver/runner.py, which is the
only process that executed anything the agent wrote.  Nothing in this file imports,
execs or subprocesses agent code: it reads that JSON as hostile input and grades it
against /tests/gt.json, which is root-only and was never visible to the run, and against
the meter's tape, which the run could not read either and did not write.

Five things are checked, and all of them must hold:

  1. The ground truth itself.  Before any comparison, every recorded sequence, span,
     forward count and trace is re-proved by tests/oracle.py, a naive replay that shares
     no code with the tree: its own encoder, its own template, its own network, a full
     encode of every render and no reuse anywhere.  The expected answers are therefore
     what a loop that never took a shortcut produces, not what the reference happened to
     emit.

  2. The token sequences.  Each episode's finished sequence must equal what a full
     render encodes to.  An encode resumed from a position the merge table does not
     protect re-merges across the seam and lands somewhere else.

  3. The trainable spans.  A turn owns the run of positions from its first generated
     one up to the first place the finished sequence stops agreeing with what the
     sampler was conditioned on.  Both directions fail: a span that runs past that point
     hands the trainer tokens the policy never chose, and a span that stops short throws
     away positions that survived intact.  A turn a retry discarded owns nothing.

  4. The work.  Characters handed to the tokenizer, calls made to it, and network
     forwards.  All three are counted inside modules the agent may not edit, so they
     measure real work whatever the submitted implementation looks like.  This is the
     axis a merely safe loop fails: encoding every render from character zero is
     correct on all of the above and wrong here.

     None of the three numbers is graded as reported, and none of the evidence they are
     derived from lives in the run.  A counter in the run's own process is a number the
     submission can assign to; a string handed to the tokenizer can carry a length of its
     own; a list the tokenizer appends to can be emptied and refilled with something
     more flattering.  The last of those is how a probe passed an earlier build - it
     encoded every render whole, searched for a legal resume with the shipped tokenizer,
     and then rewrote the record to describe only the tail it wished it had asked for.

     So the encoder and the network are served by tests/meter.py, over a socket, as
     root, and the meter writes down what it was asked for as it answers.  The figures
     are worked out here from that tape - see tests/audit.py - and the tape is replayed
     against the sealed encoder render by render: one encode per render, each one a tail
     of the render it accounts for, its ids what encoding that tail comes to, and the
     render's sequence reachable by splicing it onto ids the loop had already produced.
     Exploratory encodes have nowhere to hide, because they are on the tape too and the
     scenarios account for every event on it.  What the run reported still has to agree
     with what the meter served, so a submission has to be consistent in two places at
     once and the tape is the one it cannot reach.

     The character count is graded as a window, not as a number, and neither end of it
     is the reference's own figure.  "Resume at the last position the merge table
     protects" has several correct readings - the character after the seam never sits
     anywhere but at the front of a symbol, the character before it never sits anywhere
     but at the end of one, either of those, or the finer question of which adjacent
     pairs no symbol carries at all - and they hand the tokenizer different numbers of
     characters on the same scenario.  The floor is what the cheapest legal resume costs
     on each render, found by the oracle by trying resume positions rather than by
     reading the table, so nothing correct can come in under it however finely it reads.
     The ceiling is what the one-sided readings cost.  Insisting on one number inside
     that range would grade which reading a solver settled on rather than the work they
     did; authoring/variants/ holds the readings that must all pass.

  5. The tape itself.  There has to be one, it has to account for every render, and
     nothing may be left over on it.  A run that never asked the meter for anything
     produced its sequences some other way, whatever its report says.

Per-scenario notes on which reading of the rule each case is aimed at are on AIM below.
"""

import json
import os

import pytest

import audit
import oracle
import scen

OUT_PATH = os.environ.get("RUN_OUT", "/work/out.json")
GT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gt.json")
TAPE_PATH = os.environ.get("RUN_TAPE",
                           os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "tape.jsonl"))

NAMES = [s["name"] for s in scen.SCENARIOS]

# What each scenario is aimed at. Kept next to the data so a failure report says which
# reading of the rule broke, not just which numbers moved.
AIM = {
    "one-turn": "a single reply with nothing appended after it: the whole generated run "
                "has to stay trainable and the first encode is the only expensive one",
    "append": "one tool result appended after a reply, so the reply's tail is re-encoded "
              "in company it did not have when it was sampled",
    "two-tools": "two tool results in a row, and a second reply whose own prompt moved "
                 "underneath it, which takes the whole turn out of the record",
    "short-reply": "replies capped so short they survive the render whole: nothing may "
                   "be dropped from either span",
    "truncated": "replies that hit their cap instead of stopping, so the block "
                 "terminator in the render is a character the policy never chose",
    "no-anchor": "tool results carrying no position the table protects, so the resume "
                 "has to walk a long way back and the sequence still has to come out "
                 "right",
    "anchor-dense": "tool results full of protected positions, where a loop that walks "
                    "back further than it needs to pays for every character twice",
    "back-reach": "replies whose first character lets the marker in front of them be "
                  "pulled into the same symbol, so the seam itself is not a place an "
                  "encode may be picked up from",
    "retry": "a discarded turn: it contributes no trainable positions, and the render "
             "it left behind is shorter than the one already encoded",
    "retry-late": "a discard in the middle of a longer episode, with turns on both "
                  "sides of it that must keep their own positions",
    "interleave": "two episodes sharing one loop, each with its own cached render",
    "long": "every case at once over a long op list",
}


def load_json(path):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


GT = load_json(GT_PATH)
RUN = load_json(OUT_PATH)


def report(name):
    """The run's report for one scenario, or None if the run produced nothing usable."""
    if not isinstance(RUN, dict):
        return None
    reps = RUN.get("reports")
    if not isinstance(reps, dict):
        return None
    rep = reps.get(name)
    if not isinstance(rep, dict):
        return None
    return rep


def expected(name):
    return GT["scenarios"][name]


PROOFS = {}
LEDGER = {}


def proof(name):
    """The sealed replay of one scenario, computed once."""
    if name not in PROOFS:
        PROOFS[name] = oracle.replay(scen.by_name(name)["ops"])
    return PROOFS[name]


def ledger():
    """The meter's tape, walked against every scenario in the order they were driven.

    Read once. If there is no tape at all the run never asked the meter for anything,
    which is a run that produced its sequences some other way, and every scenario carries
    that as its complaint.
    """
    if not LEDGER:
        try:
            rows = audit.read(TAPE_PATH)
        except audit.Bad as exc:
            LEDGER.update({"rows": None, "why": str(exc), "left": None,
                           "acct": dict((n, (None, str(exc))) for n in NAMES)})
        else:
            acct, left = audit.account(rows, [(n, proof(n)) for n in NAMES])
            LEDGER.update({"rows": rows, "why": None, "left": left, "acct": acct})
    return LEDGER


def derived(name):
    """The accounting worked out again from the meter's tape, or the reason not.

    Returns (result, complaint): exactly one of the two is None.
    """
    return ledger()["acct"][name]


def as_map(value):
    """Coerce a value the run supplied into a plain dict of lists, or None."""
    if not isinstance(value, dict):
        return None
    out = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, list):
            return None
        out[key] = item
    return out


def test_ground_truth_present():
    assert isinstance(GT, dict) and GT.get("scenarios"), "ground truth missing"
    assert set(GT["scenarios"]) == set(NAMES), "ground truth does not cover the scenarios"


@pytest.mark.parametrize("name", NAMES)
def test_ground_truth_is_what_a_naive_loop_produces(name):
    """Re-prove the expected answers without the tree.

    The sealed replay encodes every render whole and reuses nothing, so its sequences
    and spans are what the trainer would get from a loop with no shortcut in it at all.
    Ground truth that did not match this would be the reference's opinion rather than
    the truth, and the token check below would mean nothing.
    """
    pf = proof(name)
    want = expected(name)
    assert want["ids"] == {k: list(v) for k, v in pf["ids"].items()}, (
        "%s: recorded sequences are not what a full encode produces" % name)
    assert want["spans"] == {k: [list(s) for s in v] for k, v in pf["spans"].items()}, (
        "%s: recorded spans are not what the naive replay owns" % name)
    assert want["fwd"] == pf["fwd"], "%s: recorded forward count is not reproducible" % name
    assert want["enc_calls"] == len(pf["renders"]), (
        "%s: recorded call count is not one per render" % name)
    assert want["enc_chars_min"] == pf["floor"], (
        "%s: recorded character floor is not what the sealed replay counts" % name)
    assert want["enc_chars_min"] <= want["enc_chars"] <= want["enc_chars_max"], (
        "%s: the recorded window does not contain the reference" % name)
    assert want["trace"] == pf["trace"], "%s: recorded trace is not reproducible" % name


def test_run_completed():
    """The loop has to survive every scenario; a crash or a hang is a failed run."""
    assert isinstance(RUN, dict), "no usable run output at %s" % OUT_PATH
    errs = RUN.get("errors") or {}
    assert not errs, "loop raised in: %s" % ", ".join(sorted(errs))
    assert set((RUN.get("reports") or {})) == set(NAMES), "not every scenario reported"


@pytest.mark.parametrize("name", NAMES)
def test_tokens(name):
    """Every episode's finished sequence must be what a full render encodes to."""
    rep = report(name)
    assert rep is not None, "no report for %s (%s)" % (name, AIM[name])
    got = as_map(rep.get("ids"))
    assert got is not None, "%s: report carries no usable sequence map" % name
    want = expected(name)["ids"]
    assert set(got) == set(want), "%s: wrong episode set" % name
    for eid in sorted(want):
        assert list(got[eid]) == list(want[eid]), (
            "%s: episode %s encoded to %r, expected %r (%s)"
            % (name, eid, got[eid], want[eid], AIM[name]))


@pytest.mark.parametrize("name", NAMES)
def test_trainable_spans(name):
    """The exact run of positions each surviving turn owns.

    Checked as a list, in turn order, so a loop that keeps a discarded turn or drops a
    surviving one fails here rather than averaging out.
    """
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    got = as_map(rep.get("spans"))
    assert got is not None, "%s: report carries no usable span map" % name
    want = expected(name)["spans"]
    assert set(got) == set(want), "%s: wrong episode set in spans" % name
    for eid in sorted(want):
        rows = got[eid]
        assert all(isinstance(r, list) and len(r) == 2 for r in rows), (
            "%s: episode %s spans are malformed: %r" % (name, eid, rows))
        assert [list(r) for r in rows] == [list(r) for r in want[eid]], (
            "%s: episode %s owns %r, expected %r (%s)"
            % (name, eid, rows, want[eid], AIM[name]))


def test_the_meter_saw_the_run():
    """There has to be a tape, and it has to be the only thing the meter was asked for.

    An empty tape is a loop that never asked the meter to encode anything, which is a
    loop whose sequences came from somewhere else. Events left over after every scenario
    has been accounted for are work nothing asked for - the exploratory encodes a search
    needs, or a second connection - and they are refused rather than ignored.
    """
    book = ledger()
    assert book["rows"], book["why"] or "the meter's tape is empty"
    assert book["left"] is None, book["left"]


@pytest.mark.parametrize("name", NAMES)
def test_meter_tape_accounts_for_the_run(name):
    """Every render's sequence has to come out of a resume the meter watched happen.

    The tape is replayed against the sealed encoder: one encode per render, each one's
    text a tail of the render it belongs to, each one's ids what encoding that text comes
    to, and the render's full sequence reachable by splicing it onto a prefix of ids the
    loop had already produced. That is the resume condition itself, checked where it was
    used rather than where it did damage. The evidence is the meter's, not the run's:
    tests/meter.py wrote it down as it served each request, from outside the process that
    made them.
    """
    result, why = derived(name)
    assert result is not None, "%s: %s (%s)" % (name, why, AIM[name])


@pytest.mark.parametrize("name", NAMES)
def test_report_agrees_with_the_meter(name):
    """What the tokenizer says it was given has to be what the meter was asked for.

    The run's own record is not evidence any more, but a disagreement between it and the
    tape is still a submission describing a run other than the one it did.
    """
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    result, why = derived(name)
    assert result is not None, "%s: %s" % (name, why)
    got = rep.get("log")
    assert isinstance(got, list), "%s: the run kept no record of what it encoded" % name
    seen = [[str(t), [int(i) for i in ids]] for t, ids in result["log"]]
    try:
        mine = [[str(item[0]), [int(i) for i in item[1]]] for item in got]
    except (TypeError, ValueError, IndexError):
        mine = None
    assert mine == seen, (
        "%s: the tokenizer's own record does not match what the meter was asked for"
        % name)


@pytest.mark.parametrize("name", NAMES)
def test_work_done(name):
    """The accounting.

    The three figures are re-derived on this side from the meter's tape - the characters
    by counting them here, the calls by counting encodes, the forwards by counting the
    steps the meter served inside this scenario's stretch of it - so they are real work
    however the submission is written, and what the run reported has to agree with them. A loop that re-encodes
    whole renders is right about every token and wrong here; one that resumes from a
    position the table does not protect is cheap here and wrong about the tokens.

    Calls and forwards are exact: one render is one call, and the forward count follows
    from the loop's own lifecycle. Characters are a window, for the reason on the module
    docstring - above the ceiling the loop is walking back past resume points that were
    there, below the floor no resume can account for the ids it produced, and inside it
    the number belongs to the solver.
    """
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    want = expected(name)
    result, why = derived(name)
    assert result is not None, "%s: %s (%s)" % (name, why, AIM[name])
    assert result["fwd"] == want["fwd"], (
        "%s: the meter served %d forwards, expected %d (%s)"
        % (name, result["fwd"], want["fwd"], AIM[name]))
    assert rep.get("fwd") == result["fwd"], (
        "%s: the run reported %r forwards against %d the meter served"
        % (name, rep.get("fwd"), result["fwd"]))
    assert result["calls"] == want["enc_calls"], (
        "%s: the meter was asked to encode %d times, expected %d (%s)"
        % (name, result["calls"], want["enc_calls"], AIM[name]))
    assert rep.get("enc_calls") == result["calls"], (
        "%s: the run reported %r calls against %d the meter served"
        % (name, rep.get("enc_calls"), result["calls"]))
    chars = result["chars"]
    assert rep.get("enc_chars") == chars, (
        "%s: the run reported %r characters against %d the meter was given"
        % (name, rep.get("enc_chars"), chars))
    assert chars >= want["enc_chars_min"], (
        "%s: %d characters reached the meter against a floor of %d, which is what the "
        "cheapest legal resume of these renders costs, so the ids were not produced by "
        "resuming an encode (%s)"
        % (name, chars, want["enc_chars_min"], AIM[name]))
    assert chars <= want["enc_chars_max"], (
        "%s: %d characters reached the meter against a ceiling of %d (%s)"
        % (name, chars, want["enc_chars_max"], AIM[name]))


@pytest.mark.parametrize("name", NAMES)
def test_trace(name):
    """Episode lifecycle, in order, as the loop recorded it."""
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    got = rep.get("trace")
    assert isinstance(got, list), "%s: report carries no trace" % name
    assert [str(e) for e in got] == expected(name)["trace"], (
        "%s: lifecycle diverged\n got %r\nwant %r" % (name, got, expected(name)["trace"]))
