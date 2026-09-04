"""Which lines a revision keeps, and which of them sit inside its change.

Both answers come off the script the tool itself settled. That matters more
than it looks. Several scripts of the same length exist for almost any pair of
revisions of a file that repeats its lines, and they disagree about which copy
of a repeated line survived, so a mapping rebuilt here from an ordinary
longest-common-subsequence walk is a different answer to a different question
and moves the note to a different line.

A change is not the set of lines the script added. It reaches across the kept
lines that sit between its runs, so a line can come through a revision
untouched and still be part of the change somebody has to read, which is what
`grp.spans` settles.
"""

from scr import grp, pin


def kept(before, after):
    out = {}
    for kind, i, j in pin.reading(before, after, pin.script(before, after)):
        if kind == "K":
            out[i] = j
    return out


def raised(line, before, after):
    for chunk in grp.spans(before, after):
        if line in chunk:
            return True
    return False
