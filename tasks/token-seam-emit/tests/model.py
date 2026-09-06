"""A second model of the release machine, built to be fast enough to grade the wide family.

`oracle.py` recomputes everything from scratch at every step, which is the right shape for
proving the contract but is quadratic, and the wide requests exist precisely because
quadratic does not fit. So the wide family is graded against this instead.

This is not the reference with the names changed. The reference remembers the index it
already found and resumes its scan in a window behind the tail; this walks the text one byte
at a time through a keyword automaton built from the stop set, where the state after each
byte is the longest suffix of the text that is a prefix of some stop string. Both the
earliest occurrence and the earliest live partial fall out of that walk rather than being
searched for, and the character boundary is carried forward the same way.

`authoring/token-seam-emit/agree.py` is what keeps the three honest: on every narrow request
the reference, `oracle.py` and this module have to produce the same rows, so the fast model
is only trusted where the naive one has already agreed with it many thousands of times.
"""


from bisect import bisect_right
from collections import deque


def build(stops):
    """A keyword automaton over the stop set: goto table, failure links, depths, ends."""
    pats = [p for p in stops if p]
    goto = [{}]
    depth = [0]
    end = [-1]
    for p in pats:
        node = 0
        for b in p:
            nxt = goto[node].get(b)
            if nxt is None:
                goto.append({})
                depth.append(depth[node] + 1)
                end.append(-1)
                nxt = len(goto) - 1
                goto[node][b] = nxt
            node = nxt
        # The longest pattern completing here, because among occurrences ending at one
        # position the longest is the one that starts earliest.
        if len(p) > end[node]:
            end[node] = len(p)

    fail = [0] * len(goto)
    queue = deque()
    for b in sorted(goto[0]):
        child = goto[0][b]
        fail[child] = 0
        queue.append(child)
    while queue:
        node = queue.popleft()
        # Breadth first, so the failure link was settled before this node is read: a state
        # that ends a shorter stop is terminal too, and the longest of them wins.
        f = fail[node]
        if end[f] > end[node]:
            end[node] = end[f]
        for b in sorted(goto[node]):
            child = goto[node][b]
            f = fail[node]
            while f and b not in goto[f]:
                f = fail[f]
            nxt = goto[f].get(b, 0)
            fail[child] = nxt if nxt != child else 0
            queue.append(child)
    return goto, fail, depth, end


def step_state(goto, fail, node, b):
    while node and b not in goto[node]:
        node = fail[node]
    return goto[node].get(b, 0)


def declared_len(c):
    if c < 0xC0:
        return 1
    if c < 0xE0:
        return 2
    if c < 0xF0:
        return 3
    return 4


def rows(name, spec, pieces, special, eos):
    """The complete record list for one request, in one forward pass."""
    floor, cap, stops, ids = spec
    goto, fail, depth, end = build(stops)

    text = bytearray()
    node = 0
    full = -1
    partial = 0
    need = 0
    marks = [0]

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
            for byte in b:
                text.append(byte)
                if need == 0:
                    need = declared_len(byte)
                need -= 1
                if need == 0:
                    marks.append(len(text))
                node = step_state(goto, fail, node, byte)
                if end[node] > 0:
                    # A longer stop completing later can still start earlier than one
                    # already seen, so this is a minimum rather than a first sighting.
                    cand = len(text) - end[node]
                    if full < 0 or cand < full:
                        full = cand
            partial = len(text) - depth[node]

        last = step == len(run)

        if full >= 0 and step >= floor:
            out.append(em(name, step, bytes(text[sent:full])))
            out.append("%s fi %d stop" % (name, step))
            return out

        ceiling = len(text) if full < 0 else full
        if partial < ceiling:
            ceiling = partial
        here = marks[bisect_right(marks, ceiling) - 1]

        if (tid == eos and step >= floor) or last:
            here = marks[-1]
            out.append(em(name, step, bytes(text[sent:here])))
            reason = "eos" if (tid == eos and step >= floor) else "length"
            out.append("%s fi %d %s" % (name, step, reason))
            return out

        out.append(em(name, step, bytes(text[sent:here])))
        sent = here
    return out


def em(name, step, b):
    return "%s em %d %s" % (name, step, b.hex() if b else "-")
