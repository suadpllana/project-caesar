"""Independent model of the release machine, written from the contract, not from the
reference.

Every quantity here is recomputed from scratch at every step: the client text is rebuilt
from the piece table, the earliest complete occurrence is found by scanning every position,
the earliest live partial is found by scanning every suffix, and the character boundary is
found by walking characters from the start of the text. Nothing is cached and nothing is
carried between steps.

That is deliberate. The reference solution carries incremental state for all three, so a
disagreement between the two implementations is a real disagreement about the contract
rather than two copies of one mistake. It also makes this module the naive baseline the
scale gate is measured against: it is the implementation an agent writes first, it is
semantically correct, and it is quadratic in the length of the request.
"""


def declared_len(c):
    """Bytes in the character a lead byte opens, from the lead byte alone.

    The contract fixes the length at the lead byte and does not revisit it, so a malformed
    sequence still consumes its declared width. Continuation bytes and ASCII are width 1.
    """
    if c < 0xC0:
        return 1
    if c < 0xE0:
        return 2
    if c < 0xF0:
        return 3
    return 4


def boundary(t, i):
    """Largest index at or before i that ends a complete character.

    Walks characters from the start of the text every time it is called.
    """
    p = 0
    while p < i:
        w = declared_len(t[p])
        if p + w > i:
            break
        p += w
    return p


def earliest_full(t, stops):
    """Index where the earliest complete occurrence of any stop string starts, else -1."""
    for i in range(len(t)):
        for x in stops:
            if x and t[i:i + len(x)] == x:
                return i
    return -1


def earliest_partial(t, stops):
    """Index of the earliest suffix of t that is a proper prefix of some stop string.

    Returns len(t) when no suffix can still grow into an occurrence.
    """
    n = len(t)
    for i in range(n):
        tail = t[i:]
        for x in stops:
            if len(tail) < len(x) and x[:len(tail)] == tail:
                return i
    return n


def rows(name, spec, pieces, special, eos):
    """The complete record list for one request.

    spec is (floor, cap, stops, ids). Emits one `em` row per step and exactly one `fi` row.
    """
    floor, cap, stops, ids = spec
    text = b""
    sent = 0
    seen = 0
    out = []
    run = ids[:cap]
    for j, tid in enumerate(run):
        step = j + 1
        if tid not in special:
            b = pieces[tid]
            if seen == 0 and b[:1] == b" ":
                b = b[1:]
            seen += 1
            text += b
        last = step == len(run)

        # A found occurrence terminates the request only at or after the floor, but it is
        # found by scanning the whole accumulated text, so one that completed earlier is
        # still here.
        full = earliest_full(text, stops)
        if full >= 0 and step >= floor:
            out.append(row_em(name, step, text[sent:full]))
            sent = full
            out.append("%s fi %d %s" % (name, step, "stop"))
            return out

        # Nothing at or after a standing occurrence may be released, and nothing inside a
        # suffix that could still grow into one.
        ceiling = len(text) if full < 0 else full
        partial = earliest_partial(text, stops)
        if partial < ceiling:
            ceiling = partial
        here = boundary(text, ceiling)

        # End of stream. The floor suppresses the terminator, not the piece: a suppressed
        # end-of-stream piece contributes no text and the request continues.
        if tid == eos and step >= floor:
            here = boundary(text, len(text))
            out.append(row_em(name, step, text[sent:here]))
            out.append("%s fi %d %s" % (name, step, "eos"))
            return out
        if last:
            here = boundary(text, len(text))
            out.append(row_em(name, step, text[sent:here]))
            out.append("%s fi %d %s" % (name, step, "length"))
            return out

        out.append(row_em(name, step, text[sent:here]))
        sent = here
    return out


def row_em(name, step, b):
    return "%s em %d %s" % (name, step, b.hex() if b else "-")
