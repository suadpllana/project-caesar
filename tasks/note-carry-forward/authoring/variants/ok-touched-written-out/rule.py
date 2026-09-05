"""The three questions a revision asks about one thread.

`kept` answers off the script the tool itself settled. Several scripts of the
same length exist for almost any pair of revisions of a file that repeats its
lines, and they disagree about which copy of a repeated line survived, so a
mapping rebuilt here from an ordinary longest-common-subsequence walk is a
different answer to a different question.

`touched` is about the span, not about a line: a thread hangs off a stretch of
code and the reviewer has to look again if the change reached any of it. The
change is not the lines the script added either. It reaches across the kept
lines that sit between its runs, which is what `grp.spans` settles.

`merges` is overlap, not equality. Two threads that share a single line are
looking at the same code and become one. The carry maps kept lines one to one,
so it can never bring two spans into each other; what does is a union, which
can reach a third thread neither half reached, and that is why one sweep over
the pairs does not settle it.

Which lines a change reaches is a fact about the pair of revisions and not
about the thread being asked about, so it is settled once for the pair and
answered from there. Every thread still on the board is asked at every
revision, and a board that settles it again for each of them pays for the
whole edit script once per thread instead of once per revision.
"""

from scr import grp, pin


def kept(before, after):
    out = {}
    for kind, i, j in pin.reading(before, after, pin.script(before, after)):
        if kind == "K":
            out[i] = j
    return out


_SETTLED = {}


def touched(span, before, after):
    key = (tuple(before), tuple(after))
    chunks = _SETTLED.get(key)
    if chunks is None:
        _SETTLED.clear()
        chunks = _SETTLED[key] = grp.spans(before, after)
    reached = set()
    for chunk in chunks:
        reached |= chunk
    return not span.isdisjoint(reached)


def merges(one, other):
    return bool(one & other)
