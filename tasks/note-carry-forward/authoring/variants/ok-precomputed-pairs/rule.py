"""Where a revision leaves each line, and which of them its changes reach.

Every answer here is read off the script the tool itself settled. That matters
more than it looks. Several scripts of the same length exist for almost any
pair of revisions of a file that repeats its lines, and they disagree about
which copy of a repeated line survived, so a mapping rebuilt here from a
longest-common-subsequence walk of our own is a different answer to a
different question and moves the note to a different line.

A line the script does not keep has not always gone. Inside one change the
lines that went and the lines that came pair off in order, so a replaced line
lands on its replacement and only a line left without a partner is really
gone. What counts as one change decides that pairing, and one change is not
one run of moves in the script: runs standing fewer than CONTEXT kept lines
apart are one change and they swallow the kept lines between them. That is the
grouping `grp.spans` reports, which is why it cannot be used here - it names
the lines a change came to rest on and drops the moves that say where each of
them came from, so the grouping has to be taken off the walk again.

`raised` is the one question `grp.spans` does answer. A change absorbs the
kept lines between its runs, so a line can come through a revision untouched
and still be inside the change a reviewer has to read again.
"""

from scr import grp, pin
from scr.pin import CONTEXT


def _changes(walk):
    """The moves of the script, grouped the way the tool groups them.

    Same law as `grp.spans`: a run of moves closes only once CONTEXT kept
    lines have gone by, so anything nearer joins it. The kept lines a change
    swallows are dropped here because a kept line pairs with nothing.
    """
    out = []
    cur = None
    since = CONTEXT
    for step in walk:
        if step[0] == "K":
            since += 1
            if cur is not None and since >= CONTEXT:
                out.append(cur)
                cur = None
            continue
        if cur is None:
            cur = []
        since = 0
        cur.append(step)
    if cur is not None:
        out.append(cur)
    return out


def kept(before, after):
    walk = pin.reading(before, after, pin.script(before, after))
    out = {}
    for kind, i, j in walk:
        if kind == "K":
            out[i] = j
    for change in _changes(walk):
        gone = [i for kind, i, j in change if kind == "D"]
        came = [j for kind, i, j in change if kind == "A"]
        for i, j in zip(gone, came):
            out[i] = j
    return out


def raised(line, before, after):
    for chunk in grp.spans(before, after):
        if line in chunk:
            return True
    return False
