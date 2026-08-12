"""Re-derive the work a run did, from the meter's tape, on the grading side.

No figure the run reports is taken on trust here, and since the last hardening no record
the run keeps is either. Everything in the loop's process belongs to the submission once
it starts: the tokenizer instance is reachable from the files the agent owns, its
attributes can be assigned to, a string handed to it can carry a __len__ of its own, and
a list it appends to can be emptied and refilled with something more flattering. The last
of those is not hypothetical - a probe passed an earlier build by handing the shipped
tokenizer every render whole, searching for a legal resume with it, and then rewriting the
record to describe only the tail. Every entry it wrote was true. The run just was not.

So the evidence is not collected in that process any more. tests/meter.py serves the
encoder and the network over a socket, as root, and writes down what it was asked for as
it answers. This module reads that tape and works the accounting out from it:

  * A render the loop had to encode is a render the tape has to account for, one enc
    event per render, in the order the op list reaches them across every scenario in
    turn. Extra encodes have nowhere to go - the exploratory ones a search needs land
    where the next render's entry is expected and stop being a tail of it - and missing
    encodes leave a render unaccounted for.

  * An entry's text has to be a tail of the render it accounts for, and encoding that
    tail with the sealed encoder has to come to exactly the ids the entry carries. The
    meter wrote both, so this is a statement about what the run asked for, not about what
    it later said it asked for.

  * The render's full sequence has to be reachable by splicing: some prefix of ids the
    loop had already produced, ending exactly on the character the entry starts at,
    followed by the entry's ids, coming to what a full encode of the render produces.
    That is the resume the task is about, checked at every render rather than only at the
    end.

  * The characters are counted here, with len() on the strings the meter recorded, and
    the forwards by counting the meter's fwd events inside each scenario's stretch of the
    tape. Neither number was ever in the run's hands.

The authoring harness has no meter behind it - it runs the loop straight, on the host -
so synth() builds the same tape from a local run's own record. That keeps one
implementation of the accounting rather than two, and it is why the window in
tests/gt.json is calibrated on exactly the quantity the verifier later grades.

What remains outside the reach of this is in STATE.md: a submission that carries a
byte-pair encoder of its own, encodes each render whole with it, searches for the last
position a resume would have been legal from, and asks the meter only for that tail. The
tape it leaves is honest, so it passes, and it lands on the floor. Shipping the merge
table is what the task is about, so that route stays open; it costs a full encode of every
render and an encoder written from scratch, which is more work than the intended solution
and arrives at the intended answer.
"""

import json

import oracle

ENC = "enc"
FWD = "fwd"


class Bad(Exception):
    """The tape does not account for the run."""


def read(path):
    """The meter's tape, or the reason there is none to read."""
    rows = []
    try:
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
    except OSError:
        raise Bad("the meter recorded nothing at %s, so the loop never asked it to "
                  "encode anything" % path)
    except ValueError:
        raise Bad("the meter's tape at %s is not readable as a record" % path)
    for row in rows:
        if not isinstance(row, list) or not row or not isinstance(row[0], str):
            raise Bad("malformed event on the meter's tape: %r" % (row,))
    return rows


def synth(order, reports):
    """The same tape, rebuilt from a local run that had no meter behind it.

    Only the authoring harness takes this path. The verifier reads the real thing.
    """
    tape = []
    for name in order:
        rep = (reports or {}).get(name)
        if not isinstance(rep, dict):
            continue
        for item in rep.get("log") or []:
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                tape.append(["bad", "malformed record entry"])
                continue
            tape.append([ENC, item[0], list(item[1])])
        fwd = rep.get("fwd")
        for _ in range(fwd if isinstance(fwd, int) and not isinstance(fwd, bool) else 0):
            tape.append([FWD])
    return tape


def splice(prefix, off):
    """How many of prefix's ids cover exactly off characters, or None."""
    w = 0
    k = 0
    while k < len(prefix) and w < off:
        w += len(oracle.VOCAB[prefix[k]])
        k += 1
    if w != off:
        return None
    return k


def _entry(row, name, step):
    """One enc event off the tape, coerced or refused."""
    if len(row) != 3 or not isinstance(row[1], str) or not isinstance(row[2], list):
        raise Bad("%s render %d: malformed encode on the meter's tape" % (name, step))
    for i in row[2]:
        if not isinstance(i, int) or isinstance(i, bool):
            raise Bad("%s render %d: the meter recorded %r among the ids it returned"
                      % (name, step, i))
    return row[1], list(row[2])


def _quiet(tape, at, name):
    """Advance over the meter's forwards up to the next encode, counting them."""
    fwd = 0
    while at < len(tape) and tape[at][0] != ENC:
        kind = tape[at][0]
        if kind == FWD:
            fwd += 1
        else:
            raise Bad("%s: the meter was asked for something it does not serve (%r), so "
                      "the tape does not describe a run of this loop"
                      % (name, tape[at][1] if len(tape[at]) > 1 else kind))
        at += 1
    return at, fwd


def one(name, proof, tape, at):
    """Account for one scenario's stretch of the tape."""
    renders = proof["renders"]
    pool = []
    seen = []
    chars = 0
    fwd = 0
    for step, (render, full) in enumerate(renders):
        at, n = _quiet(tape, at, name)
        fwd += n
        if at >= len(tape):
            raise Bad("%s: the meter was never asked to encode render %d of %d, so the "
                      "loop did not produce that sequence by encoding anything"
                      % (name, step, len(renders)))
        text, ids = _entry(tape[at], name, step)
        at += 1
        if oracle.encode(text) != ids:
            raise Bad("%s render %d: the meter recorded %d characters against ids that "
                      "are not what encoding them comes to" % (name, step, len(text)))
        if not render.endswith(text):
            raise Bad("%s render %d: the %d characters the meter was given are not the "
                      "tail of the render they have to account for"
                      % (name, step, len(text)))
        off = len(render) - len(text)
        if not oracle.protected(render, off):
            raise Bad("%s render %d: the encode was picked up at character %d, where the "
                      "pair %r is one a merge rule joins across, so that is not a boundary "
                      "that holds whatever text sits either side of it - it is a position "
                      "that happened to work on this render"
                      % (name, step, off, render[off - 1:off + 1]))
        if off == 0:
            got = list(ids)
        else:
            got = None
            for prefix in pool:
                k = splice(prefix, off)
                if k is None:
                    continue
                cand = list(prefix[:k]) + list(ids)
                if cand == full:
                    got = cand
                    break
            if got is None:
                raise Bad("%s render %d: nothing the loop had already encoded splices at "
                          "character %d onto the ids the meter returned, so the sequence "
                          "for this render was not produced by resuming an encode"
                          % (name, step, off))
        if got != full:
            raise Bad("%s render %d: resuming at character %d lands on a different "
                      "sequence from a full encode" % (name, step, off))
        pool.append(list(full))
        seen.append([text, list(ids)])
        chars += len(text)
    at, n = _quiet(tape, at, name)
    fwd += n
    return {"chars": chars, "calls": len(renders), "fwd": fwd, "log": seen}, at


def derive(proof, rep, name="scenario"):
    """One scenario's accounting from a local run, for the authoring harness.

    The verifier never takes this path: it reads the meter's tape. This exists so the
    window in tests/gt.json is calibrated by the same code that later grades against it.
    """
    tape = synth([name], {name: rep})
    res, at = one(name, proof, tape, 0)
    if at != len(tape):
        raise Bad("%s: %d events on the record are not accounted for"
                  % (name, len(tape) - at))
    return res


def account(tape, scenarios):
    """Walk the whole tape against every scenario, in the order the runner drives them.

    Returns (per scenario name -> (result, complaint), trailing complaint or None).
    Exactly one of result and complaint is None for each scenario.
    """
    out = {}
    at = 0
    stopped = None
    for name, proof in scenarios:
        if stopped is not None:
            out[name] = (None, "the meter's tape stopped accounting for the run at %s, "
                               "so nothing after it can be checked" % stopped)
            continue
        try:
            res, at = one(name, proof, tape, at)
        except Bad as exc:
            out[name] = (None, str(exc))
            stopped = name
            continue
        out[name] = (res, None)
    left = None
    if stopped is None and at < len(tape):
        kinds = [row[0] for row in tape[at:]]
        left = ("the meter was asked for %d more things than the scenarios account for "
                "(%s)" % (len(kinds), ", ".join(sorted(set(kinds)))))
    return out, left
