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
looking at the same code and become one; carrying makes that happen far more
often than opening does, because two spans that started apart can be squeezed
together by the deletions between them.
"""

from scr import grp, pin


def kept(before, after):
    out = {}
    for kind, i, j in pin.reading(before, after, pin.script(before, after)):
        if kind == "K":
            out[i] = j
    return out


def touched(span, before, after):
    for chunk in grp.spans(before, after):
        if span & chunk:
            return True
    return False


def merges(one, other):
    return bool(one & other)
