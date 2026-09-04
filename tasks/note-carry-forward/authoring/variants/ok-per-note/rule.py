"""Which lines a script keeps, and which of them sit inside a change.

`kept` reads the mapping straight off the walk the pinned engine produced.
That matters more than it looks: several scripts of the same length exist for
almost any pair whose lines repeat, and they disagree about which copy of a
repeated line survived. Rebuilding the mapping from a textbook diff, or from
the opcodes the standard library's matcher returns, answers a different
question and moves the note to a different line.

`raised` asks whether a line the script kept nevertheless falls inside one of
the changes of that same script. It can: a change absorbs the kept lines that
sit between its runs, so a line can survive the revision untouched and still
be part of the change the reviewer has to look at again.
"""


def kept(walk):
    out = {}
    for kind, i, j in walk:
        if kind == "K":
            out[i] = j
    return out


def raised(line, spans):
    for s in spans:
        if line in s:
            return True
    return False
