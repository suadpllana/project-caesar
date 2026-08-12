"""Re-derive the work a run did, from evidence, on the grading side.

A counter the run reports is a number the run chose. Everything in the loop's process
belongs to the submission once it starts: the tokenizer instance is reachable from the
files the agent owns, its attributes can be assigned to, and a string handed to it can
carry a __len__ of its own that has nothing to do with how many characters come out of
it. So no reported figure is taken on trust here. The tokenizer keeps a record of what
it actually consumed and what it handed back for each call, and this module replays that
record against the sealed oracle and works the accounting out again from scratch.

The replay is what makes the record self-checking rather than another number to trust:

  * A render the loop had to encode is a render the record has to account for, one entry
    per render, in the order the op list reaches them. The oracle knows that list.

  * An entry's text has to be a tail of the render it accounts for, and encoding that
    tail with the oracle's own encoder has to come to exactly the ids the entry carries.
    An entry shortened after the fact to make the meter look better stops matching its
    own ids here.

  * The render's full sequence has to be reachable by splicing: some prefix of ids the
    loop had already produced, ending exactly on the character the entry starts at,
    followed by the entry's ids, coming to what a full encode of the render produces.
    That is the resume the task is about, checked at every render rather than only at
    the end, and a submission that resumed from a position the merge table does not
    protect fails it where it happened rather than wherever the damage surfaced.

  * The characters are then counted here, with len() on plain strings that came through
    JSON, so a width the submission fabricated inside its own process is not in play.

What remains outside the reach of this - a submission that carries a byte pair encoder
of its own, searches each render for the last position a resume would have been legal
from, and records that - is noted in STATE.md. It costs a full encode of every render to
find, which is the work the meter exists to charge for, and no in-process meter can see
it happen; every other route to a cheap-looking record is closed here.
"""

import oracle


class Bad(Exception):
    """The record does not account for the run."""


def entries(rep):
    """The tokenizer's record, coerced from hostile JSON or refused."""
    raw = rep.get("log")
    if not isinstance(raw, list):
        raise Bad("the run carries no record of what the tokenizer was given")
    out = []
    for item in raw:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise Bad("malformed entry in the tokenizer's record: %r" % (item,))
        text, ids = item
        if not isinstance(text, str):
            raise Bad("an entry records %r as the text encoded" % (text,))
        if not isinstance(ids, list):
            raise Bad("an entry records %r as the ids returned" % (ids,))
        for i in ids:
            if not isinstance(i, int) or isinstance(i, bool):
                raise Bad("an entry records %r among the ids returned" % (i,))
        out.append((text, list(ids)))
    return out


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


def derive(proof, rep):
    """Work the accounting out again from the record, or raise Bad.

    proof is one scenario's sealed replay; rep is what the run reported.
    """
    log = entries(rep)
    renders = proof["renders"]
    if len(log) != len(renders):
        raise Bad("the tokenizer was called %d times for %d renders"
                  % (len(log), len(renders)))

    pool = []
    chars = 0
    for step, ((render, full), (text, ids)) in enumerate(zip(renders, log)):
        if oracle.encode(text) != ids:
            raise Bad("render %d: the record says %d characters produced ids that are "
                      "not what encoding them comes to" % (step, len(text)))
        if not render.endswith(text):
            raise Bad("render %d: the record's %d characters are not the tail of the "
                      "render they have to account for" % (step, len(text)))
        off = len(render) - len(text)
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
                raise Bad("render %d: nothing the loop had already encoded splices at "
                          "character %d onto the ids the record carries, so the "
                          "sequence for this render was not produced by resuming an "
                          "encode" % (step, off))
        if got != full:
            raise Bad("render %d: resuming at character %d lands on a different "
                      "sequence from a full encode" % (step, off))
        pool.append(list(full))
        chars += len(text)

    return {"chars": chars, "calls": len(log)}
